from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseCRUD
from database.models import Feedback


class FeedbackCRUD(BaseCRUD):
    """CRUD для обратной связи."""

    def __init__(self, session: AsyncSession):
        super().__init__(Feedback, session)
