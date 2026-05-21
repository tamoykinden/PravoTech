from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import FeedbackCRUD
from database.models import Feedback
from tg_bot.services.base import BaseService


class FeedbackService(BaseService):
    """Сервис для обратной связи."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.crud = FeedbackCRUD(session)

    async def save_feedback(self, user_id: int, message: str) -> Feedback:
        """
        Сохранить обратную связь от пользователя.

        Args:
            user_id: ID пользователя в БД.
            message: Текст обращения.

        Returns:
            Feedback: Созданный объект обратной связи.
        """

        return await self.crud.create(user_id=user_id, message=message)