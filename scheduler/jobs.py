from sqlalchemy import select
from bot.loader import bot
from database.connection import get_db
from database.models import User, UserSettings
from services.alert_service import alert_service
from services.ai_forecast_service import ai_forecast_service
from services.price_service import price_service
from utils.formatters import format_usd
from utils.logger import logger


def job_price_monitoring() -> None:
    """Centralized price monitoring job executed every X seconds."""
    try:
        with get_db() as session:
            current_price, prev_ref = price_service.fetch_and_record_price(session)
            # Check alerts
            sent_count = alert_service.check_and_dispatch_alerts(
                session=session,
                current_price=current_price,
                bot_instance=bot
            )
            if sent_count > 0:
                logger.info(f"Dispatched {sent_count} price alerts at price {format_usd(current_price)}")
    except Exception as e:
        logger.error(f"Error in price monitoring job: {e}")


def job_scheduled_ai_analysis() -> None:
    """Scheduled AI market analysis executed every 60 minutes with user broadcast."""
    logger.info("Executing scheduled hourly AI market analysis...")
    try:
        with get_db() as session:
            # Refresh AI analysis globally
            report_text, _ = ai_forecast_service.get_or_generate_forecast(
                session=session,
                user_id=0,
                user_tz="Asia/Tashkent",
                force_refresh=True
            )
            logger.info("Scheduled AI market analysis generated successfully.")

            # Broadcast to all active users with AI notifications enabled
            stmt = (
                select(User)
                .join(UserSettings, User.id == UserSettings.user_id)
                .where(User.is_active.is_(True), UserSettings.ai_enabled.is_(True))
            )
            users = list(session.execute(stmt).scalars().all())
            sent_count = 0
            for u in users:
                try:
                    msg = f"🔔 <b>SOATLIK AVTOMATIK AI PROGNOZ</b>\n\n{report_text}"
                    bot.send_message(chat_id=u.telegram_id, text=msg, parse_mode="HTML")
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Could not send hourly AI forecast to user {u.telegram_id}: {e}")

            logger.info(f"Broadcasted hourly AI forecast to {sent_count} users.")
    except Exception as e:
        logger.error(f"Error in scheduled AI analysis job: {e}")
