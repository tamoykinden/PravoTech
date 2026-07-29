"""Добавляет индекс безопасного полнотекстового поиска.

Revision ID: 20260722_0001
Revises: a1b2c3d4e5f6
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = '20260722_0001'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Добавляет GIN-индекс для полнотекстового поиска."""

    op.create_index(
        'ix_cases_search_vector',
        'cases',
        ['search_vector'],
        postgresql_using='gin',
    )


def downgrade() -> None:
    """Удаляет индекс полнотекстового поиска."""

    op.drop_index('ix_cases_search_vector', table_name='cases')
