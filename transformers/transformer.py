from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
from utils.logs.logs import logger
from models.bet_save import BetSaveStandard


class BaseTransformer(ABC):
    """
    Abstract base class for all data transformers.

    This class defines the general structure for transforming and validating
    parsed data before it is processed or loaded into storage.
    The workflow:
        1. Validate incoming data (ensure correct types, structure, etc.)
        2. Optionally perform calculations or adjustments
        3. Standardize the output into a defined Pydantic model (BetSaveStandard)

    Notes for developers:
    - The transform() method orchestrates the full pipeline.
    - Each step (validate, calculate, standardize) can be a no-op if not required.
    - The final output must always conform to the BetSaveStandard model.
    """

    @abstractmethod
    async def validate_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Abstract method responsible for data validation.

        Developer responsibilities:
        - Receives parsed data from a parser (either a single dict or {"data": [...]})
        - Validate each item using a Pydantic model (e.g., input-specific schema)
          Example:
              validated = InputModel(**item)
        - If the data contains a list, iterate and validate each record.
        - Return validated data as plain Python dict(s), preserving original structure.
        - If validation is not needed, simply return the input data unchanged.
        """

        pass

    @abstractmethod
    async def calculate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Abstract method for performing calculations or adjustments.

        Developer responsibilities:
        - Receives already validated data.
        - Apply any required calculations, e.g., profit margins, conversion rates, aggregates.
        - Return updated data in the same structure as input.
        - If no calculations are needed, return the input data unchanged.
        """
        pass

    @abstractmethod
    async def standardize(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> BetSaveStandard:
        """
        Abstract method for data standardization to the defined Pydantic model.

        Developer responsibilities:
        - Receives processed data (validated and optionally calculated).
        - Transform and map fields to match the BetSaveStandard schema.
          Example:
              {"profit_usd": 12.3, "user": "alex"} ->
              BetSaveStandard(profit=12.3, currency="USD", username="alex")
        - Return the standardized data as an instance of BetSaveStandard.
        - The output of this method is strictly expected to conform to BetSaveStandard.
        """
        pass

    async def transform(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> BetSaveStandard:
        """
        Executes the full transformation pipeline step by step.

        Order of execution:
            1. validate_data()
            2. calculate()
            3. standardize()

        Notes:
        - Each step can be a no-op if not required.
        - The final output must be a BetSaveStandard Pydantic model instance.
        - External modules should always call this method to convert raw parser output
          into a clean, validated, calculated, and standardized structure ready for storage.
        """

        logger.info("Transformer pipeline started.")
        logger.debug("Input data type: %s", type(data).__name__)

        try:
            logger.info("Step 1/3: validation started.")
            validated_data = await self.validate_data(data)
            logger.info("Step 1/3: validation finished.")
            logger.debug("Validated data type: %s", type(validated_data).__name__)

            logger.info("Step 2/3: calculations started.")
            calculated_data = await self.calculate(validated_data)
            logger.info("Step 2/3: calculations finished.")
            logger.debug("Calculated data type: %s", type(calculated_data).__name__)

            logger.info("Step 3/3: standardization started.")
            standardized_data = await self.standardize(calculated_data)
            logger.info("Step 3/3: standardization finished.")
            logger.debug("Standardized data type: %s", type(standardized_data).__name__)

            logger.info("Transformer pipeline completed successfully.")
            return standardized_data

        except Exception as exc:
            logger.exception("Transformer pipeline failed with an exception: %s", exc)
            raise
