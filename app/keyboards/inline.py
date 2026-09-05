"""Inline Keyboards definitions."""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.database.models import Product


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Return the main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                "⚡ Tạo tài khoản (Miễn phí)",
                callback_data="create_account",
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 Cửa Hàng",
                callback_data="shop_menu",
            ),
            InlineKeyboardButton(
                "💳 Nạp Tiền",
                callback_data="deposit_menu",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 Lịch sử đơn hàng",
                callback_data="order_history",
            ),
            InlineKeyboardButton(
                "🎁 Giới thiệu bạn bè",
                callback_data="referral_info",
            ),
        ],
        [
            InlineKeyboardButton(
                "🆔 Thông tin tài khoản",
                callback_data="account_info",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trial_choice_keyboard() -> InlineKeyboardMarkup:
    """Return the keyboard with 'Có' and 'Không' buttons for trial choice."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Có, tạo trial", callback_data="trial_yes"),
            InlineKeyboardButton("❌ Không", callback_data="trial_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_join_group_keyboard(chat_url: str) -> InlineKeyboardMarkup:
    """Return keyboard asking user to join required group and verify membership."""
    keyboard = [
        [
            InlineKeyboardButton("📢 Tham gia nhóm", url=chat_url)
        ],
        [
            InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="verify_membership")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_shop_keyboard(products: List[Product]) -> InlineKeyboardMarkup:
    """Return keyboard listing all active shop products."""
    keyboard = []
    for p in products:
        stock_str = f"Kho: {p.stock_count}" if p.stock_count > 0 else "Hết hàng"
        btn_text = f"{p.name} - {p.price:,}đ ({stock_str})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_product_{p.id}")])

    keyboard.append([
        InlineKeyboardButton("💳 Nạp Tiền", callback_data="deposit_menu"),
        InlineKeyboardButton("🔙 Quay lại Menu", callback_data="back_main_menu"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_product_confirm_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Return confirmation keyboard before purchasing a product."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Xác nhận mua ngay", callback_data=f"confirm_buy_{product_id}"),
        ],
        [
            InlineKeyboardButton("🔙 Quay lại Cửa Hàng", callback_data="shop_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_deposit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Return deposit actions keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Kiểm tra đã chuyển tiền", callback_data="check_deposit"),
        ],
        [
            InlineKeyboardButton("🛒 Đến Cửa Hàng", callback_data="shop_menu"),
            InlineKeyboardButton("🔙 Menu Chính", callback_data="back_main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple back to main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 Quay lại Menu Chính", callback_data="back_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


