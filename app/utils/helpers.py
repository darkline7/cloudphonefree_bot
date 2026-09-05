"""Helper utilities for text formatting, escaping and rendering."""

import asyncio
import html
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def escape_html(text: Any) -> str:
    """Escape HTML special characters to prevent Telegram formatting issues / injections."""
    return html.escape(str(text))


async def auto_delete_message(message, delay: int = 15) -> None:
    """Schedule a bot message for auto-deletion after `delay` seconds.

    Silently ignores errors (message already deleted, chat not found, etc.).
    """
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except Exception:
        pass


async def send_and_delete(
    bot,
    chat_id: int,
    text: str,
    delay: int = 15,
    **kwargs,
):
    """Send a message and schedule it for auto-deletion after `delay` seconds.

    Returns the sent Message object.  All extra kwargs are forwarded to
    ``bot.send_message`` (e.g. parse_mode, reply_markup).
    """
    msg = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    asyncio.create_task(auto_delete_message(msg, delay=delay))
    return msg


def format_account_stats(stats_data: Dict[str, Any]) -> str:
    """Format total accounts and user breakdown for /thongke admin command."""
    total = stats_data.get("total", 0)
    users = stats_data.get("users", {})

    lines: List[str] = [f"📊 <b>Tổng tài khoản đã tạo:</b> {total}\n"]

    if total > 0 and users:
        lines.append("<b>Chi tiết theo người dùng:</b>")
        for uid, data in users.items():
            username = escape_html(data.get("username") or "không có")
            accounts = data.get("accounts", [])
            lines.append(f"👤 <b>@{username}</b> (ID: <code>{uid}</code>): {len(accounts)} tài khoản")
            for acc in accounts:
                lines.append(f"   ▫️ <code>{escape_html(acc)}</code>")
    else:
        lines.append("<i>Chưa có tài khoản nào được tạo.</i>")

    return "\n".join(lines)


async def is_user_member_of_chat(bot, user_id: int, chat_id: int) -> bool:
    """Check if user is a member of the required group or channel."""
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        # Statuses that count as membership: 'creator', 'administrator', 'member', 'restricted' (if still in chat)
        if member.status in ("creator", "administrator", "member", "restricted"):
            return True
        return False
    except Exception:
        # If bot cannot check or user is not in chat (e.g. UserNotParticipant)
        return False

