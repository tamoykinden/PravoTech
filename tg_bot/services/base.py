from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Базовый класс для всех сервисов."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """

        self.session = session
