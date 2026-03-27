"""Add onboarding_profile and is_onboarded to user_settings

Revision ID: 001
Revises: 
Create Date: 2026-03-27

Supabase'deki user_settings tablosuna onboarding wizard verisini tutacak iki sütun ekler:
  - onboarding_profile: JSONB  (level, goal, riskTolerance)
  - is_onboarded: BOOLEAN DEFAULT FALSE
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# ── Revision metadata ──────────────────────────────────────────────────────────
revision = "001"
down_revision = None   # İlk migration — önceki revision yok
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    user_settings tablosuna iki yeni sütun ekler.

    IF NOT EXISTS kullanılmasının nedeni: Supabase projesinde tablo daha önce
    Supabase UI üzerinden oluşturulduysa bu migration'ın tekrar güvenle
    çalışabilmesi içindir. PostgreSQL 9.6+ destekler.
    """
    op.execute(
        """
        ALTER TABLE user_settings
          ADD COLUMN IF NOT EXISTS onboarding_profile JSONB,
          ADD COLUMN IF NOT EXISTS is_onboarded       BOOLEAN NOT NULL DEFAULT FALSE;
        """
    )

    # Mevcut kayıtlar için geriye dönük uyumluluk:
    # is_onboarded = FALSE (default) → wizard'ı atlamamış kabul edilir.
    # Gerekirse burada bir UPDATE ile mevcut kullanıcıları onboarded sayabilirsiniz:
    # op.execute("UPDATE user_settings SET is_onboarded = TRUE WHERE onboarding_profile IS NOT NULL;")


def downgrade() -> None:
    """
    Migration geri alındığında eklenen sütunları kaldırır.
    DİKKAT: Bu işlem sütun içindeki TÜM veriyi siler. Üretim ortamında dikkatli kullanın.
    """
    op.execute(
        """
        ALTER TABLE user_settings
          DROP COLUMN IF EXISTS is_onboarded,
          DROP COLUMN IF EXISTS onboarding_profile;
        """
    )
