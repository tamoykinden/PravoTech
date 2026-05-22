from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
from tg_bot.services.feedback import FeedbackService


class FeedbackStates(StatesGroup):
    waiting_for_message = State()


class FeedbackHandler(BaseHandlers):
    """Обработчик обратной связи."""

    def __init__(self):
        self.router = Router()
        self.router.message(F.text == ButtonConfig.FEEDBACK)(self.start_feedback)
        self.router.message(FeedbackStates.waiting_for_message, F.text)(self.save_feedback)

    async def start_feedback(self, message: Message, state: FSMContext):
        """Начать обратную связь."""

        await state.set_state(FeedbackStates.waiting_for_message)
        await message.answer(
            MessageConfig.FEEDBACK,
            reply_markup=BackKeyboard().get_markup()
        )

    async def save_feedback(self, message: Message, state: FSMContext, session: AsyncSession, user_id: int):
        """Сохранить обратную связь."""

        feedback_text = message.text.strip()

        if feedback_text == ButtonConfig.BACK:
            await state.clear()
            await message.answer(
                MessageConfig.FEEDBACK_CANCEL,
                reply_markup=MainMenuKeyboard().get_markup()
            )
            return

        if len(feedback_text) < 5:
            await message.answer(MessageConfig.PLEASE_FOR_FEEDBACK)
            return

        service = FeedbackService(session)
        await service.save_feedback(user_id, feedback_text)

        await state.clear()
        await message.answer(
            MessageConfig.THANKS_FOR_FEEDBACK,
            reply_markup=MainMenuKeyboard().get_markup()
        )


feedback_handler = FeedbackHandler()
feedback_router = feedback_handler.router
