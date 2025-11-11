from typing import Union, Dict, Any, List
from models.bet_save import BetSaveStandard
from transformers.transformer import BaseTransformer


class TransformerStake(BaseTransformer):

    async def validate_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[
        Dict[str, Any], List[Dict[str, Any]]]:
        # TODO: Разработчику
        # 1. Этот метод должен выполнять валидацию входных данных, полученных от парсера.
        # 2. Если data — это список словарей (например {"data": [...]}) — нужно пройтись циклом по каждому элементу.
        # 3. Каждый элемент должен быть передан в Pydantic модель для валидации.
        #    Например:
        #        validated = BetSaveStandard(**item)
        #        item = validated.model_dump()
        # 4. Если data — одиночный словарь, передать его напрямую в модель Pydantic.
        # 5. Вернуть валидированные данные в той же структуре, что и пришли (список или словарь).
        # 6. Если валидация не требуется для конкретного случая — вернуть data как есть.
        pass

    async def calculate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[
        Dict[str, Any], List[Dict[str, Any]]]:
        # TODO: Разработчику
        # 1. Этот метод выполняет любые необходимые расчеты или преобразования данных.
        # 2. Пример расчетов: подсчет прибыли, конвертация валют, суммирование ставок.
        # 3. Если data — список, пройтись по каждому словарю и обновить значения.
        # 4. Если data — одиночный словарь, выполнить расчеты напрямую.
        # 5. Вернуть данные в той же структуре, что и пришли (список или словарь).
        # 6. Если расчет не нужен для этого трансформера — вернуть data как есть.
        pass

    async def standardize(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> BetSaveStandard:
        # TODO: Разработчику
        # 1. Этот метод преобразует данные к единому стандарту для дальнейшей загрузки.
        # 2. Все поля должны быть приведены к формату, ожидаемому моделью BetSaveStandard.
        #    Например: {"profit_usd": 12.3} -> BetSaveStandard(profit=12.3, currency="USD")
        # 3. Если data — список, возможно нужно агрегировать или взять первый элемент в зависимости от логики.
        # 4. Вернуть объект BetSaveStandard (обязательно), чтобы downstream компоненты получали предсказуемый формат.
        # 5. Если стандартизация не требуется для конкретного случая — нужно все равно вернуть BetSaveStandard,
        #    используя исходные данные для заполнения модели.
        pass
