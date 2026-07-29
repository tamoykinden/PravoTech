"""Синхронизирует комментарии Telegram-таблиц.

Revision ID: 20260722_0002
Revises: 20260722_0001
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '20260722_0002'
down_revision: str | None = '20260722_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Уточняет назначение внешних ключей Telegram."""

    op.alter_column(
        'tg_feedback',
        'user_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
        comment='Пользователь Telegram',
        existing_comment='Пользователь',
    )
    op.alter_column(
        'tg_user_requests',
        'user_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
        comment='Пользователь Telegram',
        existing_comment='Пользователь',
    )


def downgrade() -> None:
    """Возвращает исходные комментарии."""

    for table in ('tg_feedback', 'tg_user_requests'):
        op.alter_column(
            table,
            'user_id',
            existing_type=sa.Integer(),
            existing_nullable=False,
            comment='Пользователь',
            existing_comment='Пользователь Telegram',
        )
