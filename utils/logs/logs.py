from loguru import logger

# Удаляем стандартный обработчик (консольный вывод)
logger.remove(0)

# Инициализация логирования
logger.add("logs.log", rotation="1 day", retention="7 days", compression="zip")