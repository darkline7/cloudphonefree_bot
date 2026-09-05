"""Keyboards package."""

from app.keyboards.inline import (
    get_back_to_menu_keyboard,
    get_deposit_keyboard,
    get_join_group_keyboard,
    get_main_menu_keyboard,
    get_product_confirm_keyboard,
    get_shop_keyboard,
    get_trial_choice_keyboard,
)

__all__ = [
    "get_main_menu_keyboard",
    "get_trial_choice_keyboard",
    "get_join_group_keyboard",
    "get_shop_keyboard",
    "get_product_confirm_keyboard",
    "get_deposit_keyboard",
    "get_back_to_menu_keyboard",
]
