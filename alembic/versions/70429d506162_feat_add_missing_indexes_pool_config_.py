"""feat: add missing indexes, pool config, server_default uuid

Revision ID: 70429d506162
Revises: 11c1409893d5
Create Date: 2026-06-15 19:12:06.850775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70429d506162'
down_revision: Union[str, None] = '11c1409893d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Single-column indexes ---
    op.create_index(op.f('ix_product_faqs_product_id'), 'product_faqs', ['product_id'], unique=False)

    # --- Composite + partial indexes for product filter patterns ---
    op.create_index('ix_products_category_price', 'products', ['category_id', 'price'])
    op.create_index('ix_products_stock_price', 'products', ['stock', 'price'])
    op.create_index(
        'ix_products_active_slug', 'products', ['slug'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index(
        'ix_products_active_category_price', 'products', ['category_id', 'price'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )

    # --- Server defaults for UUID primary keys (gen_random_uuid) ---
    tables = [
        'categories', 'products', 'product_specs', 'product_faqs',
        'stores', 'store_contacts', 'store_hours', 'store_social_media',
        'testimonials',
    ]
    for table in tables:
        op.alter_column(table, 'id', server_default=sa.text('gen_random_uuid()'))


def downgrade() -> None:
    # --- Server defaults ---
    tables = [
        'categories', 'products', 'product_specs', 'product_faqs',
        'stores', 'store_contacts', 'store_hours', 'store_social_media',
        'testimonials',
    ]
    for table in tables:
        op.alter_column(table, 'id', server_default=None)

    # --- Partial + composite indexes ---
    op.drop_index('ix_products_active_category_price', table_name='products')
    op.drop_index('ix_products_active_slug', table_name='products')
    op.drop_index('ix_products_stock_price', table_name='products')
    op.drop_index('ix_products_category_price', table_name='products')

    # --- Single-column indexes ---
    op.drop_index(op.f('ix_product_faqs_product_id'), table_name='product_faqs')
