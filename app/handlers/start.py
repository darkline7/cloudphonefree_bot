"""User start and id command handlers."""

import logging
from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.config import settings
from app.dependencies import container
from app.keyboards.inline import get_join_group_keyboard, get_main_menu_keyboard
from app.utils.helpers import escape_html, is_user_member_of_chat

logger = logging.getLogger(__name__)

# ── Welcome text builder ────────────────────────────────────────────
def _build_welcome_text(balance: int, remaining_turns: int) -> str:
    """Build the main welcome / menu message with Telegram-premium-style icons."""
    return (
        "✨ <b>VieCloud Shop</b> ✨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 Hệ thống tạo tài khoản Cloud Phone tự động\n\n"
        f"💎 <b>Số dư ví:</b> <code>{balance:,}đ</code>\n"
        f"⚡ <b>Lượt tạo miễn phí còn lại:</b> <code>{remaining_turns}</code> lượt\n\n"
        "📌 <i>Mỗi tài khoản được 10 lượt miễn phí. Giới thiệu bạn bè để nhận thêm +5 lượt!</i>\n\n"
        "🛒 Nạp tiền tự động qua QR & mua tài khoản bất cứ lúc nào.\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📞 Hỗ trợ: @thanhbinhdev\n"
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command: check group membership, register user and referral, display welcome menu."""
    if not update.effective_user or not update.effective_message:
        return

    user = update.effective_user

    # Parse referral code from /start <ref_id>
    referrer_id: int | None = None
    if context.args and len(context.args) > 0:
        arg = context.args[0].strip()
        if arg.isdigit():
            possible_ref = int(arg)
            if possible_ref != user.id:
                referrer_id = possible_ref

    await container.user_repo.save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referrer_id=referrer_id,
    )

    # Check required group membership
    if settings.REQUIRED_CHAT_ID:
        is_member = await is_user_member_of_chat(
            bot=context.bot,
            user_id=user.id,
            chat_id=settings.REQUIRED_CHAT_ID,
        )
        if not is_member:
            join_text = (
                "⚠️ <b>Bạn cần tham gia nhóm để có thể sử dụng bot!</b>\n\n"
                "Vui lòng nhấn nút <b>Tham gia nhóm</b> bên dưới, sau khi tham gia bấm <b>Tôi đã tham gia</b> để bắt đầu."
            )
            await update.effective_message.reply_text(
                text=join_text,
                reply_markup=get_join_group_keyboard(settings.REQUIRED_CHAT_URL),
                parse_mode=ParseMode.HTML,
            )
            return

    # Check user account quota / info
    user_data = await container.user_repo.get_user(user.id)
    created_count = await container.account_repo.get_user_created_count(user.id)
    bonus_turns = user_data.bonus_turns if user_data else 0
    balance = user_data.balance if user_data else 0
    total_allowed = 10 + bonus_turns
    remaining_turns = max(0, total_allowed - created_count)

    text = _build_welcome_text(balance, remaining_turns)

    await update.effective_message.reply_text(
        text=text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /id command: return sender's Telegram ID, username, and quota status."""
    if not update.effective_user or not update.effective_message:
        return

    user = update.effective_user

    await container.user_repo.save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    user_data = await container.user_repo.get_user(user.id)
    created_count = await container.account_repo.get_user_created_count(user.id)
    referrals_count = await container.user_repo.get_referrals_count(user.id)
    bonus_turns = user_data.bonus_turns if user_data else 0
    balance = user_data.balance if user_data else 0
    total_allowed = 10 + bonus_turns
    remaining = max(0, total_allowed - created_count)

    username_display = f"@{escape_html(user.username)}" if user.username else "không có"
    text = (
        f"🆔 <b>ID của bạn:</b> <code>{user.id}</code>\n"
        f"👤 <b>Username:</b> {username_display}\n"
        f"💎 <b>Số dư ví:</b> <code>{balance:,}đ</code>\n\n"
        f"🎯 <b>Số tài khoản đã tạo miễn phí:</b> <code>{created_count}</code>\n"
        f"👥 <b>Số người đã giới thiệu:</b> <code>{referrals_count}</code>\n"
        f"🎁 <b>Lượt thưởng nhận được:</b> <code>+{bonus_turns}</code>\n"
        f"⚡ <b>Lượt tạo miễn phí còn lại:</b> <code>{remaining}</code> lượt"
    )

    await update.effective_message.reply_text(
        text=text,
        parse_mode=ParseMode.HTML,
    )


async def setup_bot_commands(bot) -> None:
    """Set Telegram bot menu commands (the '/' menu shown in chat)."""
    commands = [
        BotCommand("start", "🏠 Menu chính"),
        BotCommand("id", "🆔 Xem thông tin tài khoản"),
    ]
    await bot.set_my_commands(commands)



