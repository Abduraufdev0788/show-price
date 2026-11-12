from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
import telebot

from database.models.user import User
from database.repositories.price_repo import PriceRepository
from database.repositories.user_repo import UserRepository
from utils.formatters import format_usd
from utils.logger import logger


class AlertService:
    @staticmethod
    def check_and_dispatch_alerts(session: Session, current_price: Decimal, bot_instance: telebot.TeleBot) -> int:
        """
        Check all active users with notification_enabled=True.
        If current_price moved beyond user's threshold from last_notified_price, send alert.
        Returns the number of notifications sent.
        """
        users: List[User] = UserRepository.get_users_with_alerts_enabled(session)
        sent_count = 0

        for user in users:
            settings = user.settings
            if not settings or not settings.notification_enabled:
                continue

            # If user has no reference price, initialize with current price
            if settings.last_notified_price is None:
                settings.last_notified_price = current_price
                continue

            ref_price = settings.last_notified_price
            diff = current_price - ref_price
            threshold = settings.price_threshold

            if abs(diff) >= threshold:
                direction = "UP" if diff > 0 else "DOWN"
                symbol_emoji = "🟢 📈" if direction == "UP" else "🔴 📉"
                diff_text = f"+{format_usd(diff)}" if diff > 0 else f"-{format_usd(abs(diff))}"
                action_text = "KO'TARILDI" if direction == "UP" else "PASAYDI"

                msg = (
                    f"🔔 <b>BTC NARXI HARAKATLANDI!</b>\n\n"
                    f"{symbol_emoji} <b>BTC {action_text}: {diff_text}</b>\n\n"
                    f"💵 <b>Yangi narx:</b> {format_usd(current_price)}\n"
                    f"📌 <b>Oldingi narx:</b> {format_usd(ref_price)}\n"
                    f"⚙️ <b>Sizning chegarangiz:</b> {format_usd(threshold)}\n"
                )

                try:
                    bot_instance.send_message(
                        chat_id=user.telegram_id,
                        text=msg,
                        parse_mode="HTML"
                    )
                    sent_count += 1

                    # Record alert in DB
                    PriceRepository.save_alert(
                        session=session,
                        user_id=user.id,
                        previous_price=ref_price,
                        current_price=current_price,
                        difference=diff,
                        direction=direction
                    )

                    # Update user's reference price to prevent duplicate alerts
                    settings.last_notified_price = current_price

                except telebot.apihelper.ApiTelegramException as e:
                    logger.warning(f"Failed to send alert to user {user.telegram_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error sending alert to {user.telegram_id}: {e}")

        return sent_count


alert_service = AlertService()

