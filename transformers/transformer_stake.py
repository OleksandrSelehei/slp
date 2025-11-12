from typing import Union, Dict, Any, List
from models.bet_save import BetSaveStandard, BetSaveStandardItem
from transformers.transformer import BaseTransformer
from models.stake import StakeItem
from utils.logs.logs import logger


class TransformerStake(BaseTransformer):

    async def validate_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[
        Dict[str, Any], List[Dict[str, Any]]]:

        validated_items: List[Dict[str, Any]] = []
        for item in data.get('data', []):
            try:
                validated = StakeItem(**item)
                validated_items.append(validated.model_dump())
            except Exception as e:
                logger.warning("⚠️ Skipping invalid item: {} | error: {}", item, e)

        logger.info("✅ Successfully validated {} items ({} skipped)", len(validated_items),
                    len(data.get('data', [])) - len(validated_items))

        return {"data": validated_items}

    async def calculate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[
        Dict[str, Any], List[Dict[str, Any]]]:
        return data

    async def standardize(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> BetSaveStandard:
        standards_items = []
        for item in data.get('data', []):
            try:
                standards_items.append(BetSaveStandardItem(**item))
            except Exception as e:
                logger.warning("⚠️ Skipping invalid item: {} | error: {}", item, e)

        return BetSaveStandard(multiple=True, items=standards_items)
