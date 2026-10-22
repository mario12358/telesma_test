"""Initial schema: books, shelves, book_shelves, notes

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("title_norm", sa.Text(), nullable=False),
        sa.Column("author_norm", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.UniqueConstraint("title_norm", "author_norm", name="uq_books_title_author"),
        sa.CheckConstraint("status IN ('to_read', 'reading', 'read')", name="ck_books_status"),
        sa.CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_books_rating_range"
        ),
        sa.CheckConstraint(
            "rating IS NULL OR status IN ('reading', 'read')", name="ck_books_rating_status"
        ),
        sqlite_strict=True,
    )
    op.create_index("ix_books_updated_at", "books", ["updated_at"])

    op.create_table(
        "shelves",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_norm", sa.Text(), nullable=False),
        sa.UniqueConstraint("name_norm", name="uq_shelves_name_norm"),
        sqlite_strict=True,
    )

    op.create_table(
        "book_shelves",
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "shelf_id",
            sa.Integer(),
            sa.ForeignKey("shelves.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sqlite_strict=True,
    )

    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sqlite_strict=True,
    )
    op.create_index("ix_notes_book_id_created_at", "notes", ["book_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notes_book_id_created_at", table_name="notes")
    op.drop_table("notes")
    op.drop_table("book_shelves")
    op.drop_table("shelves")
    op.drop_index("ix_books_updated_at", table_name="books")
    op.drop_table("books")
