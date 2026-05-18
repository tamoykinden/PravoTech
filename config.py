import os

from dotenv import load_dotenv

load_dotenv()

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
