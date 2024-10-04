import json
import os
from config.logger import logger
from datetime import datetime, time, timedelta, timezone


class CacheManager:
    def __init__(self, cache_file, request_limit, retry_after_days):
        """
        Initialize the ForvoPronunciationCache instance by loading the cache.
        """
        logger.info("Creating CacheManager")
        self.cache_file = cache_file
        self.cache = self.load_cache()
        self.request_limit = request_limit
        self.retry_after_days = retry_after_days

    def get_204_error_string(self):
        return "No pronunciations found."

    def load_cache(self):
        """
        Load the cache from the self.cache_file. If the file does not exist, initialize
        a new cache structure and save it.

        Returns:
            dict: The loaded or initialized cache.
        """
        if not os.path.exists(self.cache_file):
            logger.warning("Cache does not exist.")
            logger.warning("Initializing cache structure.")
            cache = {
                "pronunciations": {},  # word: [list of filenames]
                "failed_words": {},  # word: {"error": "Error message", "attempts": 0}
                "request_count": 0,  # Number of API requests made today
                "last_reset": datetime.today().strftime("%Y-%m-%d"),  # Last reset date
            }
            self.save_cache(cache)
            logger.info(f"Initialized new cache and saved to '{self.cache_file}'.")
            return cache
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                logger.info(f"Cache loaded successfully from '{self.cache_file}'.")
                return cache
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error while loading cache: {e}")
            # Handle corrupted cache file by reinitializing
            cache = {
                "pronunciations": {},
                "failed_words": {},
                "request_count": 0,
                "last_reset": datetime.today().strftime("%Y-%m-%d"),
            }
            self.save_cache(cache)
            return cache
        except Exception as e:
            logger.error(f"Unexpected error while loading cache: {e}")
            raise

    def save_cache(self, cache):
        """
        Save the cache to the self.cache_file using an atomic write to prevent data corruption.

        Args:
            cache (dict): The cache data to save.
        """
        temp_file = f"{self.cache_file}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
            os.replace(temp_file, self.cache_file)
            logger.info(f"Cache saved successfully to '{self.cache_file}'.")
        except Exception as e:
            logger.error(f"Failed to save cache to '{self.cache_file}': {e}")
            # Optionally, you might want to remove the temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def reset_request_count_if_new_day(self) -> dict:
        """
        Reset the request count if the current time is after 22:00 UTC and
        the last reset was before 22:00 UTC of the current day.

        Returns:
            dict: The updated cache.
        """
        # Current UTC time as a timezone-aware datetime
        now_utc = datetime.now(timezone.utc)
        reset_time_utc = time(22, 0)  # 22:00 UTC

        # Combine today's date with the reset time to get the reset datetime
        today_reset_datetime = datetime.combine(
            now_utc.date(), reset_time_utc, tzinfo=timezone.utc
        )

        # If current time is before the reset time, consider the reset time as yesterday
        if now_utc.time() < reset_time_utc:
            today_reset_datetime -= timedelta(days=1)

        last_reset_str = self.cache.get("last_reset")
        last_reset: datetime | None = None

        if last_reset_str:
            try:
                # Parse the ISO formatted datetime string into a timezone-aware datetime
                last_reset = datetime.fromisoformat(last_reset_str)
                if last_reset.tzinfo is None:
                    # Assume UTC if no timezone info is present
                    last_reset = last_reset.replace(tzinfo=timezone.utc)
                else:
                    # Convert to UTC
                    last_reset = last_reset.astimezone(timezone.utc)
            except ValueError:
                logger.error(
                    "Invalid 'last_reset' format in cache. Resetting request count."
                )
                last_reset = None

        # Determine if a reset is needed
        needs_reset = now_utc >= today_reset_datetime and (
            last_reset is None or last_reset < today_reset_datetime
        )

        if needs_reset:
            self.cache["request_count"] = 0
            # Set 'last_reset' to the reset time, not the current time
            self.cache["last_reset"] = today_reset_datetime.isoformat()
            self.save_cache(self.cache)
            logger.info("Daily request count has been reset.")
        else:
            logger.info("Daily request count does not need to be reset.")

        return self.cache

    def get_attempted_words(self):
        return self.cache.get("attempted_words", {})

    def in_attempts(self, word):
        attempted_words = self.get_attempted_words()
        is_attempted_word = attempted_words and word in attempted_words
        logger.debug(f"{word} in attempted words: {is_attempted_word}")
        return is_attempted_word

    def untried(self, word):
        untried = (
            not self.in_pronunciations(word)
            and not self.in_failures(word)
            and not self.in_attempts(word)
        )
        logger.debug(f"{word} untried? {untried}")
        return untried

    def get_failed_words(self):
        return self.cache.get("failed_words", {})

    def in_failures(self, word):
        failed_words = self.get_failed_words()
        is_failed_word = failed_words and word in failed_words
        logger.debug(f"{word} in failed words: {is_failed_word}")
        return is_failed_word

    def get_failed_word(self, word):
        failed_words = self.get_failed_words()
        if failed_words and word in failed_words:
            return word
        return None

    def get_failed_word_data(self, word):
        failed_words = self.get_failed_words()
        return failed_words.get(word, {})

    def get_last_attempt_str(self, word):
        failed_word_data = self.get_failed_word_data(word)
        if failed_word_data:
            return failed_word_data.get("last_attempt")
        return None

    def get_time_since_last_attempt(self, word):
        last_attempt_str = self.get_last_attempt_str(word)
        if last_attempt_str:
            try:
                last_attempt = datetime.strptime(last_attempt_str, "%Y-%m-%d %H:%M:%S")
                time_since_last_attempt = datetime.now() - last_attempt
                logger.warning(
                    f"Successfully determined time since last attempt for word '{word}"
                )
                return time_since_last_attempt
            except ValueError:
                logger.warning(
                    f"Invalid date format for word '{word}'. Proceeding to retry."
                )
                return None
        else:
            logger.warning(f"No 'last_attempt' found for word '{word}'")
        return None

    def is_request_limit(self):
        if self.cache.get("request_count", 0) >= self.request_limit:
            logger.warning(f"Daily request limit of {self.request_limit} reached.")
            return True
        return False

    def increment_request_count(self):
        self.cache["request_count"] = self.cache.get("request_count", 0) + 1
        self.cache["last_request"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_cache(self.cache)

    def set_last_failed_attempt(self, word):
        if "failed_words" in self.cache and word not in self.cache["pronunciations"]:
            self.cache["failed_words"][word]["last_attempt"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    def set_last_attempt(self, word):
        self.cache.setdefault("attempted_words", {}).setdefault(word, {})[
            "last_attempt"
        ] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_cache(self.cache)

    def get_request_count(self):
        return self.cache["request_count"]

    def set_request_count(self, limit):
        if not limit:
            # Update request_count to the limit
            limit = self.request_limit

        self.cache["request_count"] = limit
        self.save_cache(self.cache)

    def set_request_count_to_limit(self):
        self.cache["request_count"] = self.request_limit
        self.save_cache(self.cache)

    def increment_fetch_failure(self, word, error_str):
        """
        Increment the attempt count for a failed word by one.
        Creates failed_words[word].attempts / .error / .last_attempt if they don't exist
        """
        try:
            self.cache.setdefault("failed_words", {})[word] = {
                "error": error_str,
                "attempts": self.cache.get("failed_words", {})
                .get(word, {})
                .get("attempts", 0)
                + 1,
                "last_attempt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.save_cache(self.cache)
        except Exception as e:
            logger.exception(e)

    def log_failed_words(self):
        if "failed_words" in self.cache and self.cache["failed_words"]:
            logger.info(f"Total failed words: {len(self.cache['failed_words'])}")
            for word, details in self.cache["failed_words"].items():
                logger.info(f"Word: {word}, Details: {details}")

    def get_all_pronunciations(self):
        return self.cache.get("pronunciations", {})

    def get_pronunciations(self, word):
        pronunciations = self.cache.get("pronunciations", {})

        if word in pronunciations:
            word_pronunciations = pronunciations.get(word)
            return word_pronunciations
        return None

    def in_pronunciations(self, word):
        pronunciations = self.cache.get("pronunciations", {})
        word_in_pronunciations = word in pronunciations
        logger.debug(f"{word} in pronunciations: {word_in_pronunciations}")
        return word_in_pronunciations

    def can_reattempt(self, word):
        time_since_last_attempt = self.get_time_since_last_attempt(word)
        logger.info(f"last attempt was {time_since_last_attempt.days} days ago.")
        if time_since_last_attempt and time_since_last_attempt < timedelta(
            days=self.retry_after_days
        ):
            return False
        return True

    def set_unfailed(self, word):
        # Remove from failed_words if present
        if "failed_words" in self.cache and word in self.cache["failed_words"]:
            del self.cache["failed_words"][word]

    def set_pronunciations(self, word, pronunciations):
        # Just overwrite what's there
        # structure:
        #  pronunciations: {
        # "aill": [
        #     "[sound:aill_random.mp3]"
        # ] }
        cache_pronunciations = self.cache.get("pronunciations", {})
        cache_pronunciations[word] = pronunciations
        self.save_cache(self.cache)
