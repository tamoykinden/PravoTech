from aiogram import F, Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from config import MenuConfig, MessageConfig
from database.models import TGUser
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.main_menu import (
    MainMenuKeyboard,
    PDAgreementKeyboard,
    PDRetryKeyboard,
)


class CommonHandler(BaseHandlers):
    """Обработчик общих команд."""

    def __init__(self):
        self.router = Router()
        self.router.message(Command('start'))(self.cmd_start)
        self.router.message(Command('help'))(self.cmd_help)
        self.router.message(F.text.in_(MenuConfig.START_TEXTS))(self.cmd_start_text)
        self.router.message(F.text.in_(MenuConfig.HELP_TEXTS))(self.cmd_help)
        self.router.callback_query(F.data == 'pd_agree')(self.pd_agree)
        self.router.callback_query(F.data == 'pd_disagree')(self.pd_disagree)
        self.router.callback_query(F.data == 'pd_retry')(self.pd_retry)

    async def cmd_start(self, message: types.Message, user: TGUser, session: AsyncSession):
        """Обработчик команды /start."""

        if not user.pd_agreed:
            await message.answer(
                MessageConfig.PD_AGREEMENT_TEXT,
                reply_markup=PDAgreementKeyboard().get_markup()
            )
            return

        await message.answer(
            MessageConfig.START,
            reply_markup=MainMenuKeyboard().get_markup()
        )

    async def cmd_start_text(self, message: types.Message, user: TGUser, session: AsyncSession):
        """Обработчик текстовых приветствий (Привет, Хай и т.д.)."""

        await self.cmd_start(message, user, session)

    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help."""

        await message.answer(MessageConfig.HELP)

    async def pd_agree(self, callback: types.CallbackQuery, user: TGUser, session: AsyncSession):
        """Пользователь согласился на обработку ПДн."""

        user = await session.update_consent(user.id, True)

        await callback.message.delete()
        await callback.message.answer(
            MessageConfig.START,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        await callback.answer()

    async def pd_disagree(self, callback: types.CallbackQuery):
        """Пользователь не согласился на обработку ПДн."""

        await callback.message.edit_text(
            MessageConfig.PD_DISAGREE_TEXT,
            reply_markup=PDRetryKeyboard().get_markup()
        )
        await callback.answer()

    async def pd_retry(self, callback: types.CallbackQuery):
        """Повторный запрос согласия."""

        await callback.message.edit_text(
            MessageConfig.PD_AGREEMENT_TEXT,
            reply_markup=PDAgreementKeyboard().get_markup()
        )
        await callback.answer()


common_handler = CommonHandler()
common_router = common_handler.router
