"""Telegram Bot service using aiogram — sends notifications to staff."""

import logging
from aiogram import Bot
from app.config import get_settings

logger = logging.getLogger(__name__)

_bot_instance: Bot | None = None


def get_bot() -> Bot | None:
    """Get or create the Telegram bot instance."""
    global _bot_instance
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram notifications disabled")
        return None
    if _bot_instance is None:
        _bot_instance = Bot(token=settings.telegram_bot_token)
    return _bot_instance


async def send_escalation_notification(
    chat_id: str,
    session_id: str,
    reason: str,
    customer_summary: str | None = None,
    deep_link: str | None = None,
) -> bool:
    """Send escalation notification to a staff member via Telegram.

    Args:
        chat_id: Telegram chat ID of the staff member.
        session_id: The conversation session being escalated.
        reason: Why the conversation was escalated.
        customer_summary: Brief summary of the customer's issue.
        deep_link: URL to open the conversation directly.

    Returns:
        True if message was sent successfully.
    """
    bot = get_bot()
    if not bot:
        logger.warning("Bot not available, skipping notification")
        return False

    # Build message
    lines = [
        "🔔 <b>Yêu cầu hỗ trợ mới!</b>",
        "",
        f"📋 <b>Lý do:</b> {_reason_display(reason)}",
    ]

    if customer_summary:
        lines.append(f"💬 <b>Tóm tắt:</b> {customer_summary}")

    lines.append(f"🆔 <b>Session:</b> <code>{session_id[:8]}...</code>")

    if deep_link:
        lines.append(f"\n🔗 Mở hội thoại:\n{deep_link}")

    message = "\n".join(lines)

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML",
        )
        logger.info(f"Sent escalation notification to {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification to {chat_id}: {e}")
        return False


async def send_takeover_notification(
    chat_id: str,
    session_id: str,
    staff_name: str,
) -> bool:
    """Notify customer (via staff) that a human is taking over."""
    bot = get_bot()
    if not bot:
        return False

    message = (
        f"✅ <b>{staff_name}</b> đã nhận hỗ trợ hội thoại.\n"
        f"🆔 Session: <code>{session_id[:8]}...</code>"
    )

    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Failed to send takeover notification: {e}")
        return False


async def notify_resolution(chat_id: str, session_id: str) -> bool:
    """Notify staff that an escalation has been resolved."""
    bot = get_bot()
    if not bot:
        return False

    message = (
        f"✅ Hội thoại đã được giải quyết.\n"
        f"🆔 Session: <code>{session_id[:8]}...</code>"
    )

    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Failed to send resolution notification: {e}")
        return False


def _reason_display(reason: str) -> str:
    """Convert reason code to Vietnamese display text."""
    reasons = {
        "low_confidence": "Bot không chắc chắn câu trả lời",
        "user_request": "Khách hàng yêu cầu gặp nhân viên",
        "complex_issue": "Vấn đề phức tạp cần hỗ trợ",
        "complaint": "Khách hàng khiếu nại",
        "order_issue": "Vấn đề về đơn hàng",
    }
    return reasons.get(reason, reason)
