"""product search attributes

Revision ID: 0003_product_search_attrs
Revises: 0002_add_cart_tables
Create Date: 2026-10-07

Adds category/material/specifications to products and the product_sizes and
product_customizations tables. No CheckConstraint on material (SQLite cannot
add one via ALTER TABLE); the material enum is enforced in the service layer.
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_product_search_attrs"
down_revision = "0002_add_cart_tables"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("category", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("material", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("specifications", sa.Text(), nullable=True))
        batch.create_index("ix_products_material", ["material"], unique=False)
        batch.create_index("ix_products_category", ["category"], unique=False)
        batch.create_index("ix_products_is_active", ["is_active"], unique=False)

    op.create_table(
        "product_sizes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("size", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("product_id", "size", name="uq_product_sizes_product_size"),
    )
    op.create_index("ix_product_sizes_size_product", "product_sizes", ["size", "product_id"], unique=False)

    op.create_table(
        "product_customizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("option", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("product_id", "option", name="uq_product_customizations_product_option"),
    )
    op.create_index(
        "ix_product_customizations_option_product",
        "product_customizations",
        ["option", "product_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_product_customizations_option_product", table_name="product_customizations")
    op.drop_table("product_customizations")

    op.drop_index("ix_product_sizes_size_product", table_name="product_sizes")
    op.drop_table("product_sizes")

    with op.batch_alter_table("products") as batch:
        batch.drop_index("ix_products_is_active")
        batch.drop_index("ix_products_category")
        batch.drop_index("ix_products_material")
        batch.drop_column("specifications")
        batch.drop_column("material")
        batch.drop_column("category")
