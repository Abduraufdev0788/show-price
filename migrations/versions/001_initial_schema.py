"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=64), server_default='Asia/Tashkent', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    # 2. user_settings
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('price_threshold', sa.Numeric(precision=12, scale=2), server_default='100.00', nullable=False),
        sa.Column('monitoring_interval', sa.Integer(), server_default='5', nullable=False),
        sa.Column('buy_fee_percent', sa.Numeric(precision=6, scale=4), server_default='0.1000', nullable=False),
        sa.Column('sell_fee_percent', sa.Numeric(precision=6, scale=4), server_default='0.1000', nullable=False),
        sa.Column('withdrawal_fee', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('exchange_name', sa.String(length=64), server_default='Binance', nullable=False),
        sa.Column('notification_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('ai_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('ai_analysis_interval', sa.Integer(), server_default='60', nullable=False),
        sa.Column('last_notified_price', sa.Numeric(precision=16, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'], unique=True)

    # 3. purchases
    op.create_table(
        'purchases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('investment_amount', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('investment_includes_fee', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('purchase_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('btc_quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('remaining_btc_quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('purchase_fee', sa.Numeric(precision=16, scale=4), server_default='0.0000', nullable=False),
        sa.Column('purchase_fee_percent', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('purchase_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='OPEN', nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_purchases_user_id', 'purchases', ['user_id'])
    op.create_index('ix_purchases_status', 'purchases', ['status'])

    # 4. sales
    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=True),
        sa.Column('btc_quantity_sold', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('gross_sale_amount', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('selling_fee', sa.Numeric(precision=16, scale=4), server_default='0.0000', nullable=False),
        sa.Column('net_sale_proceeds', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('allocated_cost_basis', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('gross_profit_loss', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('net_profit_loss', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('sold_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sales_user_id', 'sales', ['user_id'])
    op.create_index('ix_sales_purchase_id', 'sales', ['purchase_id'])

    # 5. transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=True),
        sa.Column('sale_id', sa.Integer(), nullable=True),
        sa.Column('transaction_type', sa.String(length=16), nullable=False),
        sa.Column('amount', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('btc_quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('fee', sa.Numeric(precision=16, scale=4), server_default='0.0000', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])

    # 6. price_history
    op.create_table(
        'price_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('exchange', sa.String(length=32), server_default='Binance', nullable=False),
        sa.Column('symbol', sa.String(length=32), server_default='BTCUSDT', nullable=False),
        sa.Column('price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_price_history_symbol', 'price_history', ['symbol'])
    op.create_index('ix_price_history_recorded_at', 'price_history', ['recorded_at'])

    # 7. price_alerts
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('previous_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('difference', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('direction', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_price_alerts_user_id', 'price_alerts', ['user_id'])

    # 8. price_monitor_state
    op.create_table(
        'price_monitor_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('exchange', sa.String(length=32), server_default='Binance', nullable=False),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('reference_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('last_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )

    # 9. ai_analyses
    op.create_table(
        'ai_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('market_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('model_name', sa.String(length=64), nullable=False),
        sa.Column('forecast_horizon', sa.String(length=16), nullable=False),
        sa.Column('lower_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('upper_price', sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column('market_direction', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.String(length=16), nullable=False),
        sa.Column('reasoning', sa.JSON(), nullable=False),
        sa.Column('risks', sa.JSON(), nullable=False),
        sa.Column('technical_indicators', sa.JSON(), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_analyses_analyzed_at', 'ai_analyses', ['analyzed_at'])
    op.create_index('ix_ai_analyses_expires_at', 'ai_analyses', ['expires_at'])

    # 10. user_ai_analyses
    op.create_table(
        'user_ai_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ai_analysis_id', sa.Integer(), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ai_analysis_id'], ['ai_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_ai_analyses_user_id', 'user_ai_analyses', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_ai_analyses')
    op.drop_table('ai_analyses')
    op.drop_table('price_monitor_state')
    op.drop_table('price_alerts')
    op.drop_table('price_history')
    op.drop_table('transactions')
    op.drop_table('sales')
    op.drop_table('purchases')
    op.drop_table('user_settings')
    op.drop_table('users')

