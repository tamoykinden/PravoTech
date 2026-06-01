import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from database.models import TGUser
from tg_bot.handlers.base import BaseHandlers
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
        self.router.callback_query(F.data == 'back_to_main_menu')(self.back_to_main_menu)

    async def start_feedback(self, message: Message, state: FSMContext):
        """Начать обратную связь."""

        await state.set_state(FeedbackStates.waiting_for_message)

        await self.cleanup_current_and_previous(message)

        prompt_msg = await message.answer(
            MessageConfig.FEEDBACK,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
            ])
        )

        await state.update_data(prompt_msg_id=prompt_msg.message_id)

    async def save_feedback(
        self,
        message: Message,
        state: FSMContext,
        session: AsyncSession,
        user: TGUser
    ):
        """Сохранить обратную связь и отправить в админ-чат."""

        feedback_text = message.text.strip()

        data = await state.get_data()
        prompt_msg_id = data.get('prompt_msg_id')
        if prompt_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
            except Exception:
                pass

        if len(feedback_text) < 5:
            await message.answer(
                MessageConfig.PLEASE_FOR_FEEDBACK,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
                ])
            )
            return

        service = FeedbackService(session)
        await service.save_feedback(user.id, feedback_text)

        admin_chat_id = os.getenv('BOT_CHAT_ID')
        if admin_chat_id:
            try:
                admin_chat_id = int(admin_chat_id)
                username = message.from_user.username or 'без username'
                await message.bot.send_message(
                    chat_id=admin_chat_id,
                    text=(
                        f'📝 Новая обратная связь!\n\n'
                        f'👤 Пользователь: @{username} (ID: {user.id})\n'
                        f'💬 Сообщение:\n{feedback_text}'
                    ),
                )
            except Exception as e:
                print(f'Ошибка отправки в админ-чат: {e}')

        await state.clear()
        await message.answer(
            MessageConfig.THANKS_FOR_FEEDBACK,
            reply_markup=MainMenuKeyboard().get_markup()
        )

    async def back_to_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Вернуться в главное меню."""

        await state.clear()
        await callback.message.delete()
        await callback.message.answer(
            MessageConfig.BACK_TO_MAIN_MENU,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        await callback.answer()


feedback_handler = FeedbackHandler()
feedback_router = feedback_handler.router
