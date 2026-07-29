"""split tg/vk users and update documents

Revision ID: a1b2c3d4e5f6
Revises: ee8bfa2056e2
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ee8bfa2056e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('users', 'tg_users')
    op.rename_table('feedback', 'tg_feedback')
    op.rename_table('user_requests', 'tg_user_requests')

    op.create_table(
        'vk_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vk_id', sa.BigInteger(), nullable=False, comment='ID пользователя VK'),
        sa.Column(
            'registered_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Дата и время регистрации',
        ),
        sa.Column(
            'last_activity',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Последняя активность',
        ),
        sa.Column(
            'pd_agreed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
            comment='Согласие на обработку персональных данных',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vk_id'),
    )

    op.create_table(
        'vk_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='Пользователь VK'),
        sa.Column('message', sa.Text(), nullable=False, comment='Текст обращения'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Дата и время отправки',
        ),
        sa.ForeignKeyConstraint(['user_id'], ['vk_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'vk_user_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='Пользователь VK'),
        sa.Column('case_id', sa.Integer(), nullable=False, comment='Кейс'),
        sa.Column(
            'viewed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Дата и время просмотра',
        ),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id']),
        sa.ForeignKeyConstraint(['user_id'], ['vk_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.alter_column(
        'documents',
        'file_id',
        new_column_name='tg_file_id',
        existing_type=sa.String(500),
        nullable=True,
    )
    op.add_column(
        'documents',
        sa.Column(
            'vk_attachment',
            sa.String(500),
            nullable=True,
            comment='VK attachment для быстрой отправки (doc{owner_id}_{id})',
        ),
    )


def downgrade() -> None:
    op.drop_column('documents', 'vk_attachment')
    op.alter_column(
        'documents',
        'tg_file_id',
        new_column_name='file_id',
        existing_type=sa.String(500),
        nullable=False,
    )

    op.drop_table('vk_user_requests')
    op.drop_table('vk_feedback')
    op.drop_table('vk_users')

    op.rename_table('tg_user_requests', 'user_requests')
    op.rename_table('tg_feedback', 'feedback')
    op.rename_table('tg_users', 'users')
