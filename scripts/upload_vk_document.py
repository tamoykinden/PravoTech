"""
Загрузка файла в документы VK и сохранение attachment в БД.

Использование:
    python scripts/upload_vk_document.py --doc-id 1 --file templates/claim.docx

Файл загружается один раз в документы сообщества.
В БД сохраняется строка attachment (doc{owner_id}_{id}) — бот отправляет её мгновенно.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from vkbottle import API

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import DBConfig
from database.base import init_connection
from vk_bot.services.document import DocumentService


async def main() -> None:
    parser = argparse.ArgumentParser(description='Загрузка документа в VK')
    parser.add_argument('--doc-id', type=int, required=True, help='ID записи в таблице documents')
    parser.add_argument('--file', type=str, required=True, help='Путь к файлу')
    args = parser.parse_args()

    load_dotenv(ROOT / '.env')

    vk_token = os.getenv('VK_BOT_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    if not vk_token:
        raise SystemExit('VK_BOT_TOKEN не найден в .env')
    if not group_id:
        raise SystemExit('VK_GROUP_ID не найден в .env')

    file_path = Path(args.file)
    if not file_path.is_file():
        raise SystemExit(f'Файл не найден: {file_path}')

    api = API(vk_token)
    db = await init_connection(DBConfig())

    async with db.session_maker() as session:
        service = DocumentService(session)
        document = await service.upload_and_save(
            api,
            doc_id=args.doc_id,
            file_path=str(file_path),
            group_id=int(group_id),
        )
        print(f'Готово: документ #{document.id} — {document.title}')
        print(f'vk_attachment: {document.vk_attachment}')

    await db.engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
