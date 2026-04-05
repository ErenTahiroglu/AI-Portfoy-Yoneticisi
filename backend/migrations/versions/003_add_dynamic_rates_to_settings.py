"""Add commission_rate and slippage_rate to user_settings

Revision ID: 003_add_dynamic_rates_to_settings
Revises: 002_add_user_events_table
Create Date: 2026-04-02

Adds columns to user_settings for dynamic transaction costs:
  - commission_rate: NUMERIC DEFAULT 0.002 (0.2%)
  - slippage_rate: NUMERIC DEFAULT 0.001 (0.1%)
"""

from alembic import op
import sqlalchemy as sa

# ── Revision metadata ──────────────────────────────────────────────────────────
revision = "003_add_dynamic_rates_to_settings"
down_revision = "002_add_user_events_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    user_settings tablosuna komisyon ve kayma oranlarını ekler.
    shadow_divergence_logs tablosuna kullanıcı bazlı takip için user_id ekler.
    """
    op.execute(
        """
        ALTER TABLE user_settings
          ADD COLUMN IF NOT EXISTS commission_rate NUMERIC DEFAULT 0.002,
          ADD COLUMN IF NOT EXISTS slippage_rate   NUMERIC DEFAULT 0.001;
          
        ALTER TABLE shadow_divergence_logs
          ADD COLUMN IF NOT EXISTS user_id UUID;
        """
    )


def downgrade() -> None:
    """
    Eklenen sütunları kaldırır.
    """
    op.execute(
        """
        ALTER TABLE user_settings
          DROP COLUMN IF EXISTS commission_rate,
          DROP COLUMN IF EXISTS slippage_rate;

        ALTER TABLE shadow_divergence_logs
          DROP COLUMN IF EXISTS user_id;
        """
    )
