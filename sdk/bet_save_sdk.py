# betsave_sdk/bet_save_sdk.py
import requests
from typing import Dict, Any, List, Optional, Union
from logs import logger


class BetSaveSDK:
    """
    Python SDK for interacting with BetSave postback API.
    Supports registration and wager tracking endpoints.
    """

    def __init__(self, token: str, base_url: str):
        """
        Initialize SDK with authentication token and base API URL.

        :param token: Authentication token for API access (if needed in the future).
        :param base_url: Base API URL, e.g. 'https://betsave-dev-backend.vercel.app/postback'
        """
        self.token = token
        self.base_url = base_url.rstrip("/")
        logger.info("Initialized BetSaveSDK with base URL: {}", self.base_url)

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal helper method to make a GET request and handle exceptions.

        :param endpoint: API endpoint path (without base URL)
        :param params: Query parameters for GET request
        :return: Parsed JSON response or structured error dict
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug("Sending GET request to {} with params {}", url, params)

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            logger.info("Request to '{}' succeeded with status {}", endpoint, response.status_code)

            try:
                return response.json()
            except ValueError:
                logger.warning("Response from '{}' is not valid JSON", endpoint)
                return {"raw_response": response.text}

        except requests.exceptions.RequestException as e:
            logger.exception("Request to '{}' failed: {}", endpoint, e)
            return {"error": str(e), "endpoint": endpoint, "params": params}

    # === Single requests ===
    def send_registration(self, subid: str, partner_id: str, clickid: str, player_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a single registration event to BetSave API.
        """
        params = {
            "subid": subid,
            "partner_id": partner_id,
            "clickid": clickid
        }
        if player_id:
            params["player_id"] = player_id

        logger.debug("Preparing registration request with params: {}", params)
        return self._make_request("registration", params)

    def send_wager(self, subid: str, partner_id: str, amount: Union[int, float], clickid: str, player_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a single wager event to BetSave API.
        """
        params = {
            "subid": subid,
            "partner_id": partner_id,
            "amount": amount,
            "clickid": clickid
        }
        if player_id:
            params["player_id"] = player_id

        logger.debug("Preparing wager request with params: {}", params)
        return self._make_request("wager", params)

    # === Bulk requests ===
    def bulk_registration(self, registrations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send multiple registration events sequentially.
        """
        logger.info("Sending bulk registration ({} entries)", len(registrations))
        results = []
        for entry in registrations:
            res = self.send_registration(**entry)
            results.append(res)
        return results

    def bulk_wager(self, wagers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send multiple wager events sequentially.
        """
        logger.info("Sending bulk wager ({} entries)", len(wagers))
        results = []
        for entry in wagers:
            res = self.send_wager(**entry)
            results.append(res)
        return results


"""
Example usage of the BetSaveSDK class.
--------------------------------------

This script demonstrates how to initialize and use the BetSave SDK
for interacting with the BetSave postback API. It shows how to send
a single registration event and handle the response.

Logging is configured via `logger_config.py` using the Loguru library:
- Logs are written to `logs.log`
- Rotated daily
- Retained for 7 days
- Compressed automatically (zip)
"""
if __name__ == '__main__':
    # ============================================================
    # Initialize the SDK
    # ============================================================
    # token: Optional authentication token if the API requires it.
    # base_url: Base URL of the BetSave postback API.
    # The SDK automatically appends the appropriate endpoint (e.g., /registration, /wager)
    # ============================================================
    sdk = BetSaveSDK(
        token="your_token_here",
        base_url="https://betsave-dev-backend.vercel.app/postback"
    )

    # ============================================================
    # Example: Sending a single registration event
    # ============================================================
    # Required parameters:
    # - subid: Internal user or campaign identifier (string)
    # - partner_id: Unique partner ID assigned by BetSave
    # - clickid: Identifier used for attribution tracking
    #
    # Optional parameter:
    # - player_id: External player identifier (optional)
    #
    # The SDK will automatically:
    # - Construct the correct API endpoint
    # - Send a GET request with the provided parameters
    # - Log the request and response to logs.log
    # - Return parsed JSON or a structured error message
    # ============================================================
    resp = sdk.send_registration(
        subid="123",
        partner_id="45",
        clickid="abc123"
    )

    # ============================================================
    # Output the response
    # ============================================================
    # The response is a dictionary, for example:
    # {
    #     "status": "success",
    #     "message": "Registration logged successfully"
    # }
    #
    # If a request fails (e.g., timeout or invalid response),
    # you’ll receive:
    # {
    #     "error": "<error details>",
    #     "endpoint": "registration",
    #     "params": {...}
    # }
    # ============================================================
    print(resp)
