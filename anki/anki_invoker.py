import requests
import json
from config.logger import logger


class AnkiInvoker:
    def __init__(self, connect_url) -> None:
        self.connect_url = connect_url
        pass

    def invoke(self, action, params=None):
        """Helper function to call AnkiConnect API with improved error handling and logging."""
        if not self.connect_url:
            raise ValueError("connect_url is not defined")

        try:
            # Make the API request with proper parameter handling
            response = requests.post(
                self.connect_url,
                json={"action": action, "version": 6, "params": params or {}},
            )

            # Raise an exception if the response code is 4xx or 5xx
            response.raise_for_status()

            # Parse the JSON response
            result = response.json()

            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed for action '{action}': {e}")
            return {"error": str(e)}
        except ValueError as e:
            logger.error(f"Failed to parse response as JSON for action '{action}': {e}")
            return {"error": f"JSON parsing error: {str(e)}"}
