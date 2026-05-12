from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import DBConfig
from logger import bot_logger


class Database:
    """Класс для управления подключением к БД.

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

    async def create_tables(self):
        """Создает таблицы в БД."""

        bot_logger.info('Создание таблиц в базе данных...')

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        bot_logger.info('Таблицы успешно созданы')

    def get_session(self):
        """Возвращает фабрику сессий."""

        return self.session_maker


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass

async def create_database(config: DBConfig)-> Database:
    """
    Создает и инициализирует подключение к базе данных.

    Args:
        config: Конфиг с параметрами подключения

    Returns:
        Database: Экземпляр класса для работы с БД
    """

    bot_logger.info('Запуск создания подключения к БД')

    db = Database(config)

    await db.create_tables()

    bot_logger.info(f'База данных подключена')

    return db
