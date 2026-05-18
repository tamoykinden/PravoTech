import sys
from typing import Any, Optional

from loguru import logger

from config import BaseConfig


class Logger:
    """
    Класс для настройки логирования.
    Реализован как синглтон (один экземпляр на всё приложение), чтобы избежать дублирования обработчиков логов.

    Attributes:
        _instance (Logger): Единственный экземпляр класса
    """

    _instance = None

    def __new__(cls):
        """
        Создаёт единственный экземпляр класса (синглтон).

        Returns:
            Logger: Единственный экземпляр логгера
        """

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self) -> None:
        """
        Настраивает обработчики логирования.

        Выполняет:
        1. Создаёт директорию для логов (если её нет)
        2. Удаляет стандартные обработчики loguru
        3. Добавляет вывод в консоль
        4. Добавляет запись в файл с ротацией и хранением 30 дней
        """

        BaseConfig.ensure_dirs()

        logger.remove()

        logger.add(
            sys.stdout,
            format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}',
            level='INFO'
        )

        logger.add(
            BaseConfig.LOGS_DIR / 'bot.log',
            rotation='1 day',
            retention='30 days',
            format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}',
            level='INFO'
        )

    def get_logger(self) -> Any:
        """
        Возвращает настроенный экземпляр loguru.

        Returns:
            logger: Настроенный объект для логирования
        """

        return logger


_logger_instance = Logger()

bot_logger = _logger_instance.get_logger()


def safe_log(
        message: str,
        level: str = "info",
        user_id: Optional[int] = None,
        **kwargs
) -> None:
    """
    Безопасное логирование без ПДн.

    Args:
        message: Текст сообщения
        level: Уровень (info, warning, error)
        user_id: Внутренний ID пользователя (не telegram_id!)
        **kwargs: Дополнительные поля

    Пример:
        safe_log("Покупка курса", user_id=user.id, amount=5000)
    """

    msg = message
    if user_id:
        msg = f"[user_{user_id}] {msg}"
    if kwargs:
        msg += f" | {kwargs}"

    getattr(bot_logger, level.lower())(msg)
