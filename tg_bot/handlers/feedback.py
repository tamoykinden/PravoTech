from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
from tg_bot.services.feedback import FeedbackService

router = Router()


class FeedbackStates(StatesGroup):
    waiting_for_message = State()


@router.message(F.text == 'Обратная связь')
async def start_feedback(message: Message, state: FSMContext):
    """Начать обратную связь."""

    await state.set_state(FeedbackStates.waiting_for_message)
    await message.answer(
        'Напишите ваше сообщение или опишите ситуацию, которой нет в боте.\n\n'
        'Мы рассмотрим и добавим её в ближайшее время.\n\n'
        'Чтобы отменить — нажмите "Назад".',
        reply_markup=BackKeyboard().get_markup()
    )


@router.message(FeedbackStates.waiting_for_message, F.text)
async def save_feedback(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User
):
    """Сохранить обратную связь."""

    feedback_text = message.text.strip()

    if feedback_text.lower() == 'Назад':
        await state.clear()
        await message.answer(
            'Обратная связь отменена.',
            reply_markup=MainMenuKeyboard().get_markup()
        )
        return

    if len(feedback_text) < 5:
        await message.answer('Пожалуйста, напишите сообщение подробнее (минимум 5 символов).')
        return

    service = FeedbackService(session)
    await service.save_feedback(user.id, feedback_text)

    await state.clear()
    await message.answer(
        'Спасибо за обратную связь! Мы обязательно рассмотрим ваше сообщение.',
        reply_markup=MainMenuKeyboard().get_markup()
    )
