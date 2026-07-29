"""Отправка Telegram-документов, полученных через backend."""

import tempfile
from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from bot_client import BackendClient, BackendError
from config import ButtonConfig, MessageConfig
from logger import bot_logger
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.case import CaseDetailKeyboard
from tg_bot.services.case import CaseService


class DocumentHandler(BaseHandlers):
    """Обработчик отправки шаблонов документов."""

    def __init__(self):
        self.router = Router()
        self.router.callback_query(F.data.startswith('doc_'))(self.send_document)
        self.router.callback_query(F.data.startswith('back_to_case_'))(
            self.back_to_case
        )

    async def send_document(self, callback: CallbackQuery, session: BackendClient):
        parts = callback.data.split('_', maxsplit=3)
        document_id = int(parts[1])
        case_id = int(parts[2]) if len(parts) > 2 else None
        origin = parts[3] if len(parts) > 3 else 'all'
        try:
            case = await session.get_case(case_id) if case_id else None
            document = (
                next(
                    (
                        item
                        for item in case.documents
                        if item.id == document_id
                    ),
                    None,
                )
                if case
                else None
            )
            if document is None:
                cases = await session.get_cases()
                document = next(
                    (
                        doc
                        for item in cases
                        for doc in item.documents
                        if doc.id == document_id
                    ),
                    None,
                )
            if document is None:
                await callback.answer(MessageConfig.NO_FIND_FILE, show_alert=True)
                return
            payload = await session.download_document(document_id)
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temporary:
                temporary.write(payload)
                path = Path(temporary.name)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=ButtonConfig.BACK_TO_CASE,
                    callback_data=(
                        f'back_to_case_{document.case_id}_{origin}'
                    ),
                )
            ]])
            await callback.message.delete()
            await callback.message.answer_document(
                document=FSInputFile(path, filename=f'{document.title}.docx'),
                caption=MessageConfig.DOCUMENT_TITLE.format(title=document.title),
                reply_markup=keyboard,
            )
        except BackendError:
            bot_logger.exception(
                'Не удалось получить документ через backend'
            )
            await callback.answer(MessageConfig.NO_FIND_FILE, show_alert=True)
            return
        finally:
            if 'path' in locals():
                path.unlink(missing_ok=True)
        await callback.answer()

    async def back_to_case(
        self,
        callback: CallbackQuery,
        session: BackendClient,
    ) -> None:
        """Возвращает пользователя от документа к его кейсу."""

        payload = callback.data.removeprefix('back_to_case_')
        case_id_text, separator, origin = payload.partition('_')
        case_id = int(case_id_text)
        if not separator:
            origin = 'all'

        try:
            service = CaseService(session)
            case, documents = await service.get_case_with_documents(case_id)
            text = await service.format_case_text(case)
        except BackendError:
            bot_logger.exception(
                'Не удалось вернуться к кейсу через backend'
            )
            await callback.answer(MessageConfig.NO_FIND_CASES, show_alert=True)
            return

        keyboard = CaseDetailKeyboard(
            documents,
            case.id,
            origin=origin,
        ).get_markup()
        self._append_origin_navigation(keyboard, origin)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=ButtonConfig.MAIN_MENU,
                callback_data='back_to_main_menu',
            )
        ])

        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()

    @staticmethod
    def _append_origin_navigation(
        keyboard: InlineKeyboardMarkup,
        origin: str,
    ) -> None:
        """Добавляет возврат на исходный экран."""

        if origin == 'search':
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=ButtonConfig.BACK_TO_SEARCH_RESULTS,
                    callback_data='back_to_search_results',
                )
            ])
            return

        if origin.startswith('cat-'):
            category_id = int(origin.removeprefix('cat-'))
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=ButtonConfig.BACK_TO_CASES,
                    callback_data=(
                        f'back_to_cases_from_cat_{category_id}'
                    ),
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=ButtonConfig.BACK_TO_CATEGORIES,
                    callback_data='back_to_categories',
                )
            ])
            return

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=ButtonConfig.BACK_TO_CASES,
                callback_data='back_to_cases',
            )
        ])


document_handler = DocumentHandler()
document_router = document_handler.router
