from http.client import responses
from typing import Union, List
from utils.logs.logs import logger
from models.bet_save import BetSaveStandard
from sdk.bet_save_sdk import BetSaveSDK


class DataLoader:
    """
    DataLoader class responsible for sending standardized data to BetSave using BetSaveSDK.

    This class accepts a Pydantic model (BetSaveStandard) and handles single or bulk
    requests automatically depending on the `multiple` flag.

    Logging is included to track request attempts and responses.
    """

    def __init__(self, sdk: BetSaveSDK):
        """
        Initialize DataLoader with an instance of BetSaveSDK.

        Args:
            sdk (BetSaveSDK): An instance of the BetSaveSDK for interacting with the API.
        """
        self.sdk = sdk

    async def send(self, data: BetSaveStandard) -> Union[dict, List[dict]]:
        """
        Send data to BetSave via the SDK.

        Handles both single and multiple records based on the `multiple` flag in
        the BetSaveStandard model.

        Args:
            data (BetSaveStandard): Standardized data ready for sending.

        Returns:
            dict or List[dict]: Response(s) from the BetSave API.
        """
        logger.info("DataLoader: Sending data, multiple=%s", data.multiple)

        if data.multiple:
            # Sending multiple entries
            payload: List[dict] = [item.model_dump() for item in data.items]
            logger.debug("DataLoader: Payload for bulk request: %s", payload)
            response = self.sdk.bulk_registration(payload)
            if response:
                response = self.sdk.bulk_wager(payload)
                logger.info("DataLoader: Bulk request completed with %d entries", len(payload))
                return response
            else:
                return []
        else:
            # Sending a single entry
            payload: dict = data.item.model_dump()
            logger.debug("DataLoader: Payload for single request: %s", payload)
            response = self.sdk.send_wager(
                subid=payload["subid"],
                partner_id=payload["partner_id"],
                amount=payload.get("amount", 0),
                clickid=payload["clickid"],
                player_id=payload.get("player_id")
            )
            logger.info("DataLoader: Single request completed for subid=%s", payload["subid"])
            return response
