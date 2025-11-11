from typing import List, Optional, Union
from pydantic import BaseModel, root_validator, Field


class BetSaveStandardItem(BaseModel):
    # TODO: Define fields for a single bet record
    subid: str  # Internal user or campaign identifier
    partner_id: str  # Unique partner ID assigned by BetSave
    clickid: str  # Identifier used for attribution tracking
    player_id: Optional[str] = None  # Optional external player identifier
    amount: Optional[float] = None  # Optional field for wager amount
    # Add any additional fields required by the API


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

    @root_validator
    def check_items_consistency(cls, values):
        multiple = values.get('multiple', False)
        item = values.get('item')
        items = values.get('items')

        if multiple:
            # If multiple=True, `items` must be a non-empty list, `item` must be None
            if not items or not isinstance(items, list):
                raise ValueError("For multiple=True, 'items' must be a non-empty list")
            if item is not None:
                raise ValueError("For multiple=True, 'item' must be None")
        else:
            # If multiple=False, `item` must be provided, `items` must be None
            if item is None:
                raise ValueError("For multiple=False, 'item' must be provided")
            if items is not None:
                raise ValueError("For multiple=False, 'items' must be None")

        return values

    def get_payload(self) -> Union[dict, List[dict]]:
        """
        Returns the data in a format ready for the BetSaveSDK:
        - If multiple=True: returns a list of dictionaries
        - If multiple=False: returns a single dictionary
        """
        if self.multiple:
            return [i.model_dump() for i in self.items]
        return self.item.model_dump()
