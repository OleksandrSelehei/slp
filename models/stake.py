from pydantic import BaseModel


class StakeItem(BaseModel):
    player_id: str
    balance: float
