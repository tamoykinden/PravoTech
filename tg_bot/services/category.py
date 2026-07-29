"""Получение категорий через центральный backend."""

from backend.schemas import CategoryRead
from tg_bot.services.base import BaseService


class CategoryService(BaseService):
    """Сервис категорий Telegram-клиента."""

    async def get_all_categories(self) -> list[CategoryRead]:
        """Возвращает все категории."""

        return await self.session.get_categories()

    async def get_category_by_id(self, category_id: int) -> CategoryRead | None:
        """Возвращает категорию по идентификатору."""

        return await self.session.get_category(category_id)
