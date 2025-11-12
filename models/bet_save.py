from typing import List, Optional, Union
from pydantic import BaseModel, root_validator, Field
from utils.config.config import config


class BetSaveStandardItem(BaseModel):

    subid: str  # Internal user or campaign identifier
    partner_id: str = config.PARTNER_ID  # Unique partner ID assigned by BetSave
    clickid: str = config.CLICKID # Identifier used for attribution tracking
    player_id: Optional[str] = None  # Optional external player identifier
    amount: Optional[float] = None  # Optional field for wager amount


class BetSaveStandard(BaseModel):
    """
    Model for storing data to be sent to BetSave.

    Can contain either a single record (`item`) or multiple records (`items`).
    Rules:
      - If multiple=False, exactly one record (`item`) must be provided
      - If multiple=True, a list of records (`items`) must be provided, and `item` must be None
    """
    multiple: bool = Field(default=False, description="True if sending multiple records")
    item: Optional[BetSaveStandardItem] = None
    items: Optional[List[BetSaveStandardItem]] = None

    def get_payload(self) -> Union[dict, List[dict]]:
        """
        Returns the data in a format ready for the BetSaveSDK:
        - If multiple=True: returns a list of dictionaries
        - If multiple=False: returns a single dictionary
        """
        if self.multiple:
            return [i.model_dump() for i in self.items]
        return self.item.model_dump()
