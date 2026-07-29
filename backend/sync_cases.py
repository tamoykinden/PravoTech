"""Ручная синхронизация юридических кейсов с Яндекс.Диском."""

import asyncio

from backend.services import YandexDiskCaseSynchronizer
from config import DBConfig
from database.base import Database
from logger import bot_logger


async def synchronize_cases() -> None:
    """Синхронизирует категории, кейсы и документы и закрывает БД."""

    database = Database(DBConfig())
    try:
        async with database.session_maker() as session:
            synchronizer = (
                YandexDiskCaseSynchronizer.from_environment()
            )
            result = await synchronizer.synchronize(session)
        bot_logger.info(
            'Синхронизация завершена: создано категорий {}, '
            'кейсов {}, перемещено {}, обновлено {}, документов {}',
            result.categories_created,
            result.cases_created,
            result.cases_moved,
            result.cases_updated,
            result.documents_created,
        )
    finally:
        await database.engine.dispose()


if __name__ == '__main__':
    asyncio.run(synchronize_cases())
