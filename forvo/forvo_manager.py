from config.config import FORVO_API_KEY, FORVO_LANGUAGE
import requests
from config.logger import logger
import time

import requests

import random
import json

# Constants for backoff
RATE_LIMIT_EXCEEDED_RETRIES = 5  # Maximum number of retries
INITIAL_BACKOFF = 1  # Initial backoff time in seconds
MAX_BACKOFF = 60  # Maximum backoff time in seconds
BACKOFF_FACTOR = 2  # Exponential factor


class ForvoManager:
    def __init__(self):
        pass

    def make_url(self, encoded_word):
        url = f"https://apifree.forvo.com/key/{FORVO_API_KEY}/format/json/action/word-pronunciations/word/{encoded_word}/language/{FORVO_LANGUAGE}"
        logger.info(url)
        return url

    def invoke(self, url, action, params=None):
        try:
            response = requests.post(
                url, json={"action": action, "version": 6, "params": params or {}}
            )
            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed for action '{action}': {e}")
            return {"error": str(e)}
        except ValueError as e:
            logger.error(f"JSON parsing failed for action '{action}': {e}")
            return {"error": f"JSON parsing error: {str(e)}"}

    def request_get(self, url):
        response = requests.get(url)
        logger.info(response)
        return response

    def encode(self, word):
        return requests.utils.quote(word)

    def filename_and_url_from_data(self, data, word):

        my_data = []

        if "items" in data and isinstance(data["items"], list):
            ## see temp.json for example of data structure
            mp3_index = 1
            for item in data["items"]:
                if item.get("pathmp3"):
                    mp3_url = item["pathmp3"]

                    # Check if mp3_url is already a full URL
                    if not mp3_url.startswith("http"):
                        # If it's a relative path, prepend the base URL
                        if not mp3_url.startswith("/"):
                            mp3_url = "/" + mp3_url
                        mp3_url = f"https://apifree.forvo.com{mp3_url}"
                        logger.info(mp3_url)

                    # Generate a unique filename
                    # dialect = item.get("dialect", "random").replace(
                    #     " ", "_"
                    # )  # Assuming 'dialect' field exists
                    username = item.get("username", "Anonymous").replace(" ", "_")
                    gender = item.get("sex", "n").replace(" ", "_")
                    filename = f"{word}_{username}_{gender}_{mp3_index}.mp3".replace(
                        "/", "_"
                    )  # Replace any '/' to avoid path issues
                    my_data.append({"filename": filename, "url": mp3_url})
                    mp3_index += 1
        return my_data

    # This is for a single word
    def fetch_pronunciations(self, word):
        encoded_word = self.encode(word)
        url = self.make_url(encoded_word)

        my_response = {
            "word": word,
            "data": [],
            "status_code": None,
            "other_error": False,
            "rate_limit_exceeded": False,
            "request_limit_reached": False,
            "message": None,
        }

        try:
            backoff = INITIAL_BACKOFF  # Initialize backoff time

            for attempt in range(1, RATE_LIMIT_EXCEEDED_RETRIES + 1):
                response = self.request_get(url)

                # Success
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except ValueError:
                        logger.error(f"Invalid JSON response for word '{word}'.")
                        my_response["message"] = response.text
                        my_response["other_error"] = True
                        # Return early
                        return my_response

                    # set 'data' to the a filename-and-url list
                    my_response["data"] = self.filename_and_url_from_data(data, word)

                    if not my_response["data"]:
                        # If that came back empty, we have no data
                        logger.warning(f"No pronunciations found for '{word}'.")
                        my_response["status_code"] = 204
                    else:
                        # Otherwise, we got some urls and filenames
                        my_response["status_code"] = 200

                    return my_response

                elif response.status_code == 429:
                    if attempt < RATE_LIMIT_EXCEEDED_RETRIES:
                        # Calculate backoff time with jitter
                        sleep_time = min(backoff, MAX_BACKOFF)
                        jitter = random.uniform(0, sleep_time * 0.1)  # 10% jitter
                        total_sleep = sleep_time + jitter

                        logger.warning(
                            f"Rate limit (429) exceeded for '{word}'. "
                            f"Attempt {attempt}/{RATE_LIMIT_EXCEEDED_RETRIES}. "
                            f"Sleeping for {total_sleep:.2f} seconds before retrying."
                        )
                        time.sleep(total_sleep)

                        # Exponentially increase the backoff time
                        backoff *= BACKOFF_FACTOR
                    else:
                        # If we exceeded number of retries allowed,
                        # Then return early.
                        logger.error(
                            f"Rate limit (429) exceeded after {RATE_LIMIT_EXCEEDED_RETRIES} attempts for '{word}'."
                        )
                        my_response["rate_limit_exceeded"] = True
                        my_response["status_code"] = 429
                        return my_response

                # Request limit reached
                elif response.status_code == 400:
                    my_response["status_code"] = 400
                    try:
                        error_message = response.json()
                    except ValueError:
                        error_message = response.text

                    if (
                        isinstance(error_message, list)
                        and "Limit/day reached." in error_message
                    ):
                        my_response["request_limit_reached"] = True
                    return my_response

                else:
                    try:
                        my_response["message"] = response.json()
                    except ValueError:
                        my_response["message"] = response.text

                    logger.error(
                        f"Error fetching Forvo data for '{word}': Status {response.status_code}, Response: {my_response['message']}"
                    )
                    my_response["other_error"] = True
                    return my_response

        except Exception as e:
            logger.exception(
                f"Exception occurred while fetching/storing Forvo data for '{word}': {e}"
            )
            return None  # Indicate failure to fetch
