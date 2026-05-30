from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Базовый класс для всех сервисов VK-бота."""

    def __init__(self, session: AsyncSession):
        self.session = session
