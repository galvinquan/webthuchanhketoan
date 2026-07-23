"""Add classroom, co-teachers, assignments; link company to assignment + grading

Revision ID: b1a2c3d4e5f6
Revises: eea852c04325
Create Date: 2026-07-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1a2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'eea852c04325'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- class_room -----
    op.create_table(
        'class_room',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('join_code', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['teacher_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('join_code'),
    )
    op.create_index(op.f('ix_class_room_id'), 'class_room', ['id'], unique=False)
    op.create_index(op.f('ix_class_room_join_code'), 'class_room', ['join_code'], unique=True)

    # ----- class_teacher (đồng giáo viên) -----
    op.create_table(
        'class_teacher',
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='co_teacher'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['class_id'], ['class_room.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('class_id', 'teacher_id'),
    )

    # ----- enrollment (SV <-> lớp) -----
    op.create_table(
        'enrollment',
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.ForeignKeyConstraint(['class_id'], ['class_room.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('class_id', 'user_id'),
    )

    # ----- assignment (bài tập trong lớp) -----
    op.create_table(
        'assignment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['class_id'], ['class_room.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignment_id'), 'assignment', ['id'], unique=False)

    # ----- company: gắn với assignment thay vì trực tiếp company<->user, thêm chấm điểm -----
    op.add_column('company', sa.Column('assignment_id', sa.Integer(), nullable=True))
    op.add_column('company', sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'))
    op.add_column('company', sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('company', sa.Column('feedback', sa.Text(), nullable=True))
    op.add_column('company', sa.Column('graded_by', sa.Integer(), nullable=True))
    op.add_column('company', sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        'fk_company_assignment_id', 'company', 'assignment', ['assignment_id'], ['id']
    )
    op.create_foreign_key(
        'fk_company_graded_by', 'company', 'app_user', ['graded_by'], ['id']
    )

    # company trước đây unique(user_id) -> đổi thành unique(user_id, assignment_id)
    op.drop_constraint('company_user_id_key', 'company', type_='unique')
    op.create_unique_constraint(
        'uq_company_user_assignment', 'company', ['user_id', 'assignment_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_company_user_assignment', 'company', type_='unique')
    op.create_unique_constraint('company_user_id_key', 'company', ['user_id'])

    op.drop_constraint('fk_company_graded_by', 'company', type_='foreignkey')
    op.drop_constraint('fk_company_assignment_id', 'company', type_='foreignkey')

    op.drop_column('company', 'graded_at')
    op.drop_column('company', 'graded_by')
    op.drop_column('company', 'feedback')
    op.drop_column('company', 'score')
    op.drop_column('company', 'status')
    op.drop_column('company', 'assignment_id')

    op.drop_index(op.f('ix_assignment_id'), table_name='assignment')
    op.drop_table('assignment')

    op.drop_table('enrollment')
    op.drop_table('class_teacher')

    op.drop_index(op.f('ix_class_room_join_code'), table_name='class_room')
    op.drop_index(op.f('ix_class_room_id'), table_name='class_room')
    op.drop_table('class_room')
