"""Handlers package."""

from app.handlers.callback import (
    handle_account_info_callback,
    handle_back_main_menu,
    handle_check_deposit_callback,
    handle_confirm_buy_callback,
    handle_create_account_callback,
    handle_deposit_menu_callback,
    handle_order_history_callback,
    handle_product_select_callback,
    handle_referral_info_callback,
    handle_shop_menu_callback,
    handle_trial_choice_callback,
    handle_verify_membership_callback,
)
from app.handlers.errors import global_error_handler
from app.handlers.start import id_handler, setup_bot_commands, start_handler

__all__ = [
    "start_handler",
    "id_handler",
    "setup_bot_commands",
    "handle_create_account_callback",
    "handle_trial_choice_callback",
    "handle_verify_membership_callback",
    "handle_referral_info_callback",
    "handle_shop_menu_callback",
    "handle_product_select_callback",
    "handle_confirm_buy_callback",
    "handle_deposit_menu_callback",
    "handle_check_deposit_callback",
    "handle_order_history_callback",
    "handle_account_info_callback",
    "handle_back_main_menu",
    "global_error_handler",
]




