"""Callback query handlers for account creation, trial confirmation, shop, and banking."""

import asyncio
import logging
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes
from app.config import settings
from app.dependencies import container
from app.keyboards.inline import (
    get_back_to_menu_keyboard,
    get_deposit_keyboard,
    get_join_group_keyboard,
    get_main_menu_keyboard,
    get_product_confirm_keyboard,
    get_shop_keyboard,
    get_trial_choice_keyboard,
)
from app.handlers.start import _build_welcome_text
from app.utils.helpers import escape_html, is_user_member_of_chat

logger = logging.getLogger(__name__)


async def handle_verify_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'verify_membership' button click."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    is_member = await is_user_member_of_chat(
        bot=context.bot,
        user_id=user.id,
        chat_id=settings.REQUIRED_CHAT_ID,
    )

    if not is_member:
        await query.answer("❌ Bạn vẫn chưa tham gia nhóm. Vui lòng tham gia nhóm trước!", show_alert=True)
        return

    await query.answer("✅ Xác minh thành công!")
    text = (
        "✨ <b>VieCloud Shop</b> ✨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 Chào mừng bạn đến với hệ thống!\n"
        "Nhấn các nút bên dưới để bắt đầu sử dụng.\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📞 Hỗ trợ: @thanhbinhdev\n"
    )
    try:
        await query.message.delete()
    except Exception:
        pass
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def handle_back_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'back_main_menu' button click."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    await query.answer()
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_data = await container.user_repo.get_user(user.id)
    created_count = await container.account_repo.get_user_created_count(user.id)
    bonus_turns = user_data.bonus_turns if user_data else 0
    balance = user_data.balance if user_data else 0
    total_allowed = 10 + bonus_turns
    remaining_turns = max(0, total_allowed - created_count)

    text = _build_welcome_text(balance, remaining_turns)

    if query.message:
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        else:
            try:
                await query.message.edit_text(
                    text=text,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )


async def handle_shop_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of products available in the shop."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    await query.answer()
    user = update.effective_user
    user_data = await container.user_repo.get_user(user.id)
    balance = user_data.balance if user_data else 0

    products = await container.shop_repo.get_all_products(active_only=True)

    text = (
        "🛒 <b>CỬA HÀNG TÀI KHOẢN CLOUD PHONE</b>\n\n"
        f"💰 <b>Số dư hiện tại của bạn:</b> <code>{balance:,}đ</code>\n\n"
        "Chọn sản phẩm bạn muốn mua bên dưới để xem chi tiết và xác nhận thanh toán tự động:"
    )

    if not products:
        text += "\n\n<i>(Hiện tại chưa có sản phẩm nào được bày bán)</i>"

    keyboard = get_shop_keyboard(products)
    if query.message:
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            try:
                await query.message.edit_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )


async def handle_product_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show details and confirm purchase for a specific product."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    data = query.data or ""
    match = re.match(r"^buy_product_(\d+)$", data)
    if not match:
        return

    product_id = int(match.group(1))
    await query.answer()

    product = await container.shop_repo.get_product(product_id)
    if not product:
        await query.answer("❌ Sản phẩm không tồn tại!", show_alert=True)
        return

    user = update.effective_user
    user_data = await container.user_repo.get_user(user.id)
    balance = user_data.balance if user_data else 0

    desc = product.description or "Không có mô tả chi tiết."
    stock_status = f"<code>{product.stock_count}</code> tài khoản" if product.stock_count > 0 else "❌ Hết hàng"

    text = (
        f"📦 <b>CHI TIẾT SẢN PHẨM</b>\n\n"
        f"🏷️ <b>Tên sản phẩm:</b> <b>{escape_html(product.name)}</b>\n"
        f"💵 <b>Giá bán:</b> <code>{product.price:,}đ</code>\n"
        f"📦 <b>Tình trạng kho:</b> {stock_status}\n"
        f"📝 <b>Mô tả:</b> {escape_html(desc)}\n\n"
        f"💰 <b>Số dư của bạn:</b> <code>{balance:,}đ</code>\n"
    )

    if product.stock_count <= 0:
        text += "\n⚠️ <i>Sản phẩm này hiện đang hết hàng. Vui lòng quay lại sau!</i>"
        keyboard = get_back_to_menu_keyboard()
    elif balance < product.price:
        text += f"\n⚠️ <i>Số dư không đủ. Bạn cần nạp thêm ít nhất <code>{(product.price - balance):,}đ</code> để mua.</i>"
        keyboard = get_deposit_keyboard(user.id)
    else:
        keyboard = get_product_confirm_keyboard(product.id)

    try:
        await query.message.edit_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )


async def handle_confirm_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process actual product purchase."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    data = query.data or ""
    match = re.match(r"^confirm_buy_(\d+)$", data)
    if not match:
        return

    product_id = int(match.group(1))
    user = update.effective_user

    await query.answer("Đang tiến hành giao dịch...")

    success, message, order = await container.shop_repo.purchase_product(
        user_id=user.id,
        username=user.username,
        product_id=product_id,
    )

    if not success or not order:
        await query.message.reply_text(
            f"❌ <b>Giao dịch thất bại:</b> {escape_html(message)}",
            parse_mode=ParseMode.HTML,
            reply_markup=get_back_to_menu_keyboard(),
        )
        return

    # Purchase success!
    text = (
        "🎉 <b>MUA HÀNG THÀNH CÔNG!</b>\n\n"
        f"🔖 <b>Mã đơn hàng:</b> <code>#{order.id}</code>\n"
        f"🏷️ <b>Sản phẩm:</b> <b>{escape_html(order.product_name)}</b>\n"
        f"💵 <b>Giá tiền:</b> <code>{order.price:,}đ</code>\n\n"
        f"🔑 <b>Thông tin tài khoản:</b>\n"
        f"<code>{escape_html(order.account_data)}</code>\n\n"
        "<i>Vui lòng lưu lại thông tin tài khoản ngay. Bạn cũng có thể xem lại tại mục 'Lịch sử đơn hàng'.</i>"
    )

    await query.message.reply_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def handle_deposit_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display VietQR image and bank transfer instructions for user."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    await query.answer()
    user = update.effective_user
    chat_id = update.effective_chat.id

    qr_url = container.bank_service.generate_vietqr_url(user_id=user.id)
    memo = f"{settings.BANK_MEMO_PREFIX} {user.id}"

    caption = (
        "💳 <b>NẠP TIỀN TỰ ĐỘNG QUA NGÂN HÀNG (ACB)</b>\n\n"
        f"🏦 <b>Ngân hàng:</b> <code>ACB (Ngân hàng Á Châu)</code>\n"
        f"💳 <b>Số tài khoản:</b> <code>{settings.BANK_ACCOUNT_NO}</code>\n"
        f"👤 <b>Chủ tài khoản:</b> <code>{settings.BANK_ACCOUNT_NAME}</code>\n"
        f"📝 <b>Nội dung chuyển khoản (BẮT BUỘC):</b> <code>{memo}</code>\n\n"
        "⚠️ <b>LƯU Ý QUAN TRỌNG:</b>\n"
        f"- Phải ghi chính xác nội dung <code>{memo}</code> để được cộng tiền tự động.\n"
        "- Hệ thống sẽ tự động cộng tiền vào tài khoản sau 10 - 30 giây kể từ khi chuyển khoản thành công.\n"
        "- Sau khi chuyển tiền xong, bạn có thể bấm <b>'Kiểm tra đã chuyển tiền'</b> bên dưới."
    )

    try:
        if query.message:
            try:
                await query.message.delete()
            except Exception:
                pass
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=qr_url,
            caption=caption,
            reply_markup=get_deposit_keyboard(user.id),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.warning("Failed to send VietQR photo: %s. Sending text fallback.", e)
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=get_deposit_keyboard(user.id),
            parse_mode=ParseMode.HTML,
        )


async def handle_check_deposit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manual trigger to re-check bank transactions for the user."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    await query.answer("Đang đồng bộ và kiểm tra lịch sử ngân hàng...")
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Trigger immediate bank scan
    count = await container.bank_service.check_transactions()
    
    user_data = await container.user_repo.get_user(user.id)
    balance = user_data.balance if user_data else 0

    if count > 0:
        await query.answer(f"✅ Đã ghi nhận giao dịch! Số dư hiện tại: {balance:,}đ", show_alert=True)
        try:
            if query.message and query.message.photo:
                await query.message.delete()
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ <b>Nạp tiền thành công!</b>\n\nSố dư ví hiện tại của bạn là: <b>{balance:,}đ</b>",
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
    else:
        await query.answer(
            f"ℹ️ Số dư hiện tại: {balance:,}đ\nChưa phát hiện giao dịch nạp tiền mới. Nếu vừa chuyển, vui lòng đợi 10 - 30 giây rồi thử lại!",
            show_alert=True,
        )


async def handle_order_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's purchased orders history."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    await query.answer()
    user = update.effective_user
    chat_id = update.effective_chat.id

    orders = await container.shop_repo.get_user_orders(user.id)
    if not orders:
        text = "📦 <b>LỊCH SỬ ĐƠN HÀNG</b>\n\nBạn chưa mua sản phẩm nào."
    else:
        text = "📦 <b>LỊCH SỬ ĐƠN HÀNG CỦA BẠN</b>\n\n"
        for o in orders[:10]:
            text += (
                f"🔖 <b>Đơn #{o.id}</b> - <b>{escape_html(o.product_name)}</b>\n"
                f"💵 Giá: <code>{o.price:,}đ</code> | 📅 {o.created_at or ''}\n"
                f"🔑 Tài khoản: <code>{escape_html(o.account_data)}</code>\n"
                "--------------------\n"
            )

    if query.message:
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        else:
            try:
                await query.message.edit_text(text=text, reply_markup=get_back_to_menu_keyboard(), parse_mode=ParseMode.HTML)
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=get_back_to_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )


async def handle_referral_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'referral_info' button click: show user's referral link and status."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    await query.answer()

    # Get bot info to generate invite link
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user.id}"

    user_data = await container.user_repo.get_user(user.id)
    created_count = await container.account_repo.get_user_created_count(user.id)
    referrals_count = await container.user_repo.get_referrals_count(user.id)
    bonus_turns = user_data.bonus_turns if user_data else 0
    total_allowed = 10 + bonus_turns
    remaining = max(0, total_allowed - created_count)

    text = (
        "🎁 <b>CHƯƠNG TRÌNH GIỚI THIỆU BẠN BÈ</b>\n\n"
        "Mỗi tài khoản Telegram mặc định được tạo <b>10 tài khoản</b>.\n"
        "Khi bạn giới thiệu một người bạn mới và người đó <b>tạo thành công 1 tài khoản</b>, bạn sẽ được cộng <b>+5 lượt tạo</b>!\n\n"
        f"🔗 <b>Link giới thiệu của bạn:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 <b>Thống kê của bạn:</b>\n"
        f"- Đã giới thiệu: <b>{referrals_count}</b> bạn bè\n"
        f"- Lượt thưởng nhận được: <b>+{bonus_turns}</b> lượt\n"
        f"- Đã tạo: <b>{created_count}/{total_allowed}</b> tài khoản\n"
        f"- Lượt tạo còn lại: <b>{remaining}</b> lượt"
    )

    if query.message:
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        else:
            try:
                await query.message.edit_text(
                    text=text,
                    reply_markup=get_back_to_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=get_back_to_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )



async def handle_create_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'create_account' button click."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    # 0. Check group membership
    if settings.REQUIRED_CHAT_ID:
        is_member = await is_user_member_of_chat(
            bot=context.bot,
            user_id=user.id,
            chat_id=settings.REQUIRED_CHAT_ID,
        )
        if not is_member:
            await query.answer("⚠️ Bạn cần tham gia nhóm trước khi dùng bot!", show_alert=True)
            join_text = (
                "⚠️ <b>Bạn cần tham gia nhóm để có thể sử dụng bot!</b>\n\n"
                "Vui lòng nhấn nút <b>Tham gia nhóm</b> bên dưới, sau khi tham gia bấm <b>Tôi đã tham gia</b> để bắt đầu."
            )
            try:
                await query.message.edit_text(
                    text=join_text,
                    reply_markup=get_join_group_keyboard(settings.REQUIRED_CHAT_URL),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=join_text,
                    reply_markup=get_join_group_keyboard(settings.REQUIRED_CHAT_URL),
                    parse_mode=ParseMode.HTML,
                )
            return


    # 1. Rate limiting check
    if container.rate_limiter.is_rate_limited(user.id):
        remaining = container.rate_limiter.remaining_cooldown(user.id)
        await query.answer(
            f"Vui lòng đợi {remaining}s trước khi thực hiện thao tác tiếp theo!",
            show_alert=True,
        )
        return

    # Check account quota limit: 10 default + bonus_turns from referrals
    user_data = await container.user_repo.get_user(user.id)
    created_count = await container.account_repo.get_user_created_count(user.id)
    bonus_turns = user_data.bonus_turns if user_data else 0
    total_allowed = 10 + bonus_turns

    if created_count >= total_allowed:
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user.id}"
        limit_text = (
            "⚠️ <b>Bạn đã hết lượt tạo tài khoản!</b>\n\n"
            f"- Đã tạo: <b>{created_count}/{total_allowed}</b> tài khoản\n\n"
            "💡 <i>Mỗi tài khoản Telegram mặc định được tạo 10 tài khoản miễn phí.</i>\n"
            "🎁 <b>Để nhận thêm +5 lượt tạo:</b> Hãy gửi link giới thiệu của bạn cho bạn bè:\n"
            f"<code>{ref_link}</code>\n"
            "Khi bạn bè tham gia và tạo thành công 1 tài khoản, bạn sẽ nhận ngay <b>+5 lượt tạo mới</b>!"
        )
        await query.answer("Bạn đã hết lượt tạo tài khoản!", show_alert=True)
        try:
            await query.message.edit_text(
                text=limit_text,
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text=limit_text,
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        return

    await query.answer("Bắt đầu tạo tài khoản...")

    # Save user to DB
    await container.user_repo.save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 Đang khởi tạo...")

    async def update_status(text: str) -> None:
        try:
            await status_msg.edit_text(text)
        except BadRequest:
            pass  # Message content identical or deleted

    try:
        # Progress transitions with smooth async sleep
        await asyncio.sleep(0.5)
        email, password, api_user_id, token, cuid = await container.account_service.create_account(
            progress_callback=update_status
        )

        # Record account in database
        await container.account_repo.record_created_account(
            user_id=user.id,
            username=user.username,
            email=email,
            api_user_id=api_user_id,
        )
        # If this is the user's first created account and they were referred, grant +5 bonus turns to referrer
        if created_count == 0 and user_data and user_data.referrer_id:
            referrer_id = user_data.referrer_id
            await container.user_repo.add_bonus_turns(referrer_id, turns=5)
            logger.info("Granted 5 bonus turns to referrer %s for referred user %s", referrer_id, user.id)
            # Notify referrer
            try:
                ref_user_name = f"@{user.username}" if user.username else (user.first_name or f"ID: {user.id}")
                notify_text = (
                    f"🎉 <b>Chúc mừng!</b> Người bạn mà bạn giới thiệu (<b>{escape_html(ref_user_name)}</b>) "
                    "đã tạo thành công 1 tài khoản mới!\n"
                    "🎁 Bạn được cộng thêm <b>+5 lượt tạo tài khoản</b>."
                )
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=notify_text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logger.warning("Could not notify referrer %s: %s", referrer_id, e)


        # Save pending session in SQLite for trial confirmation
        await container.session_repo.save_session(
            user_id=user.id,
            api_user_id=api_user_id,
            token=token,
            cuid=cuid,
        )

        success_text = (
            "✅ <b>Tạo tài khoản thành công!</b>\n\n"
            f"📧 <b>Email:</b> <code>{escape_html(email)}</code>\n"
            f"🔑 <b>Password:</b> <code>{escape_html(password)}</code>"
        )
        await status_msg.edit_text(success_text, parse_mode=ParseMode.HTML)

        # Send trial confirmation prompt
        await context.bot.send_message(
            chat_id=chat_id,
            text="Bạn có muốn tạo máy trial không?",
            reply_markup=get_trial_choice_keyboard(),
        )

    except Exception as e:
        logger.error("Error during account creation for user %s: %s", user.id, e, exc_info=True)
        try:
            await status_msg.edit_text(f"❌ Lỗi: {escape_html(str(e))}", parse_mode=ParseMode.HTML)
        except TelegramError:
            pass


async def handle_trial_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'trial_yes' and 'trial_no' button clicks."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    choice = query.data

    await query.answer("Đang xử lý...")

    if choice == "trial_no":
        try:
            await query.message.edit_text("❌ Đã bỏ qua tạo máy trial.")
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="❌ Đã bỏ qua tạo máy trial.")
        await container.session_repo.delete_session(user.id)
        return

    # Check pending session
    session = await container.session_repo.get_session(user.id)
    if not session:
        try:
            await query.message.edit_text("⚠️ Không tìm thấy thông tin tài khoản để tạo trial.")
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Không tìm thấy thông tin tài khoản để tạo trial.",
            )
        return

    try:
        await query.message.edit_text("🖥️ Đang tạo máy trial...")
    except Exception:
        pass

    try:
        ok, res = await container.willclouds_service.receive_trial(
            user_id=session.api_user_id,
            token=session.token,
            cuid=session.cuid,
        )

        if ok:
            await query.message.edit_text("✅ Tạo máy trial thành công!")
        else:
            error_msg = res.get("msg") or str(res)
            await query.message.edit_text(f"❌ Tạo trial thất bại: {escape_html(error_msg)}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error("Error during trial activation for user %s: %s", user.id, e, exc_info=True)
        await query.message.edit_text(f"❌ Lỗi: {escape_html(str(e))}", parse_mode=ParseMode.HTML)
    finally:
        await container.session_repo.delete_session(user.id)


async def handle_account_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'account_info' button click: show user's account details."""
    query = update.callback_query
    if not query or not update.effective_user or not update.effective_chat:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    await query.answer()

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
    total_deposited = user_data.total_deposited if user_data else 0
    total_allowed = 10 + bonus_turns
    remaining = max(0, total_allowed - created_count)

    username_display = f"@{escape_html(user.username)}" if user.username else "không có"
    text = (
        "🆔 <b>THÔNG TIN TÀI KHOẢN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Username:</b> {username_display}\n"
        f"🔢 <b>ID Telegram:</b> <code>{user.id}</code>\n\n"
        f"💎 <b>Số dư ví:</b> <code>{balance:,}đ</code>\n"
        f"💰 <b>Tổng đã nạp:</b> <code>{total_deposited:,}đ</code>\n\n"
        f"🎯 <b>Đã tạo miễn phí:</b> <code>{created_count}</code> tài khoản\n"
        f"👥 <b>Đã giới thiệu:</b> <code>{referrals_count}</code> bạn bè\n"
        f"🎁 <b>Lượt thưởng:</b> <code>+{bonus_turns}</code>\n"
        f"⚡ <b>Lượt còn lại:</b> <code>{remaining}</code> lượt\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    try:
        await query.message.edit_text(
            text=text,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
