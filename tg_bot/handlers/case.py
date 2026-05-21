from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from database.crud import DocumentCRUD
from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.case import CaseDetailKeyboard, CasesListKeyboard
from tg_bot.services.case import CaseService

router = Router()


@router.message(F.text == ButtonConfig.CASES)
async def list_cases(message: Message, session: AsyncSession):
    """Показать список всех кейсов."""

    service = CaseService(session)
    cases = await service.get_all_cases()

    if not cases:
        await message.answer(MessageConfig.NO_CASES)
        return

    keyboard = CasesListKeyboard(cases).get_markup()
    await message.answer(
        'Все кейсы:',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('case_'))
async def view_case(callback: CallbackQuery, session: AsyncSession):
    """Показать детали кейса и документы."""

    case_id = int(callback.data.split('_')[1])

    service = CaseService(session)
    case, documents = await service.get_case_with_documents(case_id)

    if not case:
        await callback.message.edit_text(
            MessageConfig.NO_FIND_CASES,
            reply_markup=BackKeyboard().get_markup()
        )
        await callback.answer()
        return

    text = await service.format_case_text(case)

    if documents:
        keyboard = CaseDetailKeyboard(documents, case_id).get_markup()
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=BackKeyboard().get_markup())

    await callback.answer()


@router.callback_query(F.data.startswith('doc_'))
async def send_document(callback: CallbackQuery, session: AsyncSession):
    """Отправить файл документа по file_id."""

    doc_id = int(callback.data.split('_')[1])

    doc_crud = DocumentCRUD(session)
    document = await doc_crud.get_by_id(doc_id)

    if not document or not document.file_id:
        await callback.answer(MessageConfig.NO_FIND_FILE, show_alert=True)
        return

    await callback.message.answer_document(document.file_id, caption=f'{document.title}')
    await callback.answer()


@router.callback_query(F.data == 'back_to_cases')
async def back_to_cases_list(callback: CallbackQuery, session: AsyncSession):
    """Вернуться к списку кейсов."""

    service = CaseService(session)
    cases = await service.get_all_cases()

    if not cases:
        await callback.message.edit_text(MessageConfig.NO_CASES)
        await callback.answer()
        return

    keyboard = CasesListKeyboard(cases).get_markup()
    await callback.message.edit_text('Все кейсы:', reply_markup=keyboard)
    await callback.answer()
