"""add rate constraints

Revision ID: 004
Revises: 003
Create Date: 2026-04-02 21:26:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Veritabanı seviyesinde %0-50 arası kısıtlama (CHECK CONSTRAINT) ekler."""
    op.execute(
        """
        ALTER TABLE user_settings 
        ADD CONSTRAINT check_rates_range 
        CHECK (commission_rate >= 0 AND commission_rate <= 0.5 AND slippage_rate >= 0 AND slippage_rate <= 0.5);
        """
    )


def downgrade() -> None:
    """Eklenen kısıtlamayı kaldırır."""
    op.execute(
        """
        ALTER TABLE user_settings 
        DROP CONSTRAINT IF EXISTS check_rates_range;
        """
    )
