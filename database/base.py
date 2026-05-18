from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import DBConfig
from logger import bot_logger


class Database:
    """
    Класс для управления подключением к БД.

    Создает engine и sessionmaker
    """

    def __init__(self, db_config: DBConfig):
        """Инициализация подключения к БД.

        Args:
            db_config: Конфиг с параметрами подключения
        """

        self.engine = create_async_engine(
            db_config.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )

        self.session_maker = async_sessionmaker(bind=self.engine, expire_on_commit=False)

        bot_logger.info('Движок базы данных создан')

    def get_session(self):
        """Возвращает фабрику сессий."""

        return self.session_maker


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass

async def init_connection(config: DBConfig)-> Database:
    """
    Инициализирует подключение к базе данных.

    Args:
        config: Конфиг с параметрами подключения

    Returns:
        Database: Экземпляр класса для работы с БД
    """

    bot_logger.info('Запуск подключения к БД')

    db = Database(config)

    bot_logger.info(f'База данных подключена')

    return db
