"""Application main factory and runner."""

import logging
from typing import Optional
from telegram import Bot
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)
from app.config import settings
from app.dependencies import container
from app.handlers import (
    global_error_handler,
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
    id_handler,
    setup_bot_commands,
    start_handler,
)


logger = logging.getLogger(__name__)

_bot_instance: Optional[Bot] = None


def get_bot_instance() -> Optional[Bot]:
    """Get the active Bot instance for web broadcasts."""
    return _bot_instance


def build_application() -> Application:
    """Configure and build the telegram Application (User features only)."""
    global _bot_instance
    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()
    _bot_instance = app.bot

    # Set bot in bank service for notifications
    container.bank_service.set_bot(app.bot)

    # Register User Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("id", id_handler))

    # Register Callback Query Handlers
    app.add_handler(CallbackQueryHandler(handle_create_account_callback, pattern=r"^create_account$"))
    app.add_handler(CallbackQueryHandler(handle_referral_info_callback, pattern=r"^referral_info$"))
    app.add_handler(CallbackQueryHandler(handle_trial_choice_callback, pattern=r"^(trial_yes|trial_no)$"))
    app.add_handler(CallbackQueryHandler(handle_verify_membership_callback, pattern=r"^verify_membership$"))
    app.add_handler(CallbackQueryHandler(handle_shop_menu_callback, pattern=r"^shop_menu$"))
    app.add_handler(CallbackQueryHandler(handle_product_select_callback, pattern=r"^buy_product_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_confirm_buy_callback, pattern=r"^confirm_buy_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_deposit_menu_callback, pattern=r"^deposit_menu$"))
    app.add_handler(CallbackQueryHandler(handle_check_deposit_callback, pattern=r"^check_deposit$"))
    app.add_handler(CallbackQueryHandler(handle_order_history_callback, pattern=r"^order_history$"))
    app.add_handler(CallbackQueryHandler(handle_account_info_callback, pattern=r"^account_info$"))
    app.add_handler(CallbackQueryHandler(handle_back_main_menu, pattern=r"^back_main_menu$"))

    # Register Global Error Handler
    app.add_error_handler(global_error_handler)

    return app


async def on_startup(app: Application) -> None:
    """Perform startup tasks like database migrations and cache warmups."""
    logger.info("Initializing bot dependencies...")
    await container.init()
    # Set up Telegram bot menu commands
    await setup_bot_commands(app.bot)
    # Start auto bank poller
    await container.bank_service.start_polling()
    logger.info("Bot application started successfully!")


async def on_shutdown(app: Application) -> None:
    """Perform cleanup tasks on bot shutdown."""
    logger.info("Shutting down bot dependencies...")
    await container.close()
    logger.info("Bot application shut down gracefully.")


