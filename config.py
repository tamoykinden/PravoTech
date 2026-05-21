import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Базовые настройки проекта."""

    BASE_DIR = Path(__file__).parent
    LOGS_DIR = BASE_DIR / 'logs'

    @classmethod
    def ensure_dirs(cls):
        cls.LOGS_DIR.mkdir(exist_ok=True)

class DBConfig:
    """Настройки подключения к БД."""

    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv(
        'DB_USER',
    )
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')

    @property
    def database_url(self) -> str:
        """Возвращает строку подключения к PostgreSQL."""

        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


class TextConfig:
    """Тексты сообщений бота."""

    START = (
        '👋 Привет! Я бот «ПравоТека».\n\n'
        'Я помогу вам найти пошаговые инструкции для решения типовых правовых ситуаций.\n\n'
        'Выберите действие в меню ниже:'
    )

    HELP = (
        'Справка\n\n'
        'Список кейсов — показать все доступные кейсы\n'
        'Поиск кейса — найти кейс по ключевым словам\n'
        'Категории — выбрать кейс по категории\n'
        'Обратная связь — отправить сообщение разработчикам\n\n'
        'Если у вас возникла ситуация, которой нет в боте — напишите в обратную связь, мы добавим её.'
    )
