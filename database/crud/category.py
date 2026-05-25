from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseCRUD
from database.models import CaseCategory


class CategoryCRUD(BaseCRUD):
    """CRUD для категорий."""

    def __init__(self, session: AsyncSession):
        super().__init__(CaseCategory, session)