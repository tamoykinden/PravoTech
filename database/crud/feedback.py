from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseCRUD
from database.models import TGFeedback, VKFeedback


class TGFeedbackCRUD(BaseCRUD):
    """CRUD для обратной связи Telegram."""

    def __init__(self, session: AsyncSession):
        super().__init__(TGFeedback, session)


class VKFeedbackCRUD(BaseCRUD):
    """CRUD для обратной связи VK."""

    def __init__(self, session: AsyncSession):
        super().__init__(VKFeedback, session)


FeedbackCRUD = TGFeedbackCRUD
