"""add user_events table

Revision ID: 002_add_user_events_table
Revises: 001_add_onboarding_to_user_settings
Create Date: 2026-03-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ── Revision metadata ──────────────────────────────────────────────────────────
revision = '002_add_user_events_table'
down_revision = '001_add_onboarding_to_user_settings'
branch_labels = None
depends_on = None

def upgrade():
    """
    user_events tablosunu oluşturur.
    Supabase (PostgreSQL) ortamına uygun UUID ve Foreign Key kısıtlamalarını içerir.
    """
    op.create_table(
        'user_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_settings.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_user_events_user_id', 'user_events', ['user_id'])
    op.create_index('ix_user_events_event_type', 'user_events', ['event_type'])

def downgrade():
    """
    Tabloyu ve indeksleri temizler.
    """
    op.drop_index('ix_user_events_event_type', table_name='user_events')
    op.drop_index('ix_user_events_user_id', table_name='user_events')
    op.drop_table('user_events')
