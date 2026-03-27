"""Create user_events table for telemetry

Revision ID: 002
Revises: 001
Create Date: 2026-03-27

Behavioral Brake etkileşimlerini ölçmek için kullanıcı olaylarını tutacak tablo.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# ── Revision metadata ──────────────────────────────────────────────────────────
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    """
    user_events tablosunu oluşturur. 
    Bu tablo, Behavioral Brake gibi kritik etkileşimlerin analiz edilmesi için kullanılır.
    """
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_events (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id       UUID NOT NULL,
            event_type    TEXT NOT NULL,
            event_metadata JSONB DEFAULT '{}',
            created_at    TIMESTAMPTZ DEFAULT now()
        );
        
        -- Hızlı analiz için index
        CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id);
        """
    )

def downgrade() -> None:
    """
    Migration geri alındığında tabloyu siler.
    """
    op.execute("DROP TABLE IF EXISTS user_events;")
