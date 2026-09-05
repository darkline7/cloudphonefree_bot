"""Global error handler for Telegram Bot."""

import logging
from telegram import Update
from telegram.error import BadRequest, Conflict, Forbidden, NetworkError, TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catches uncaught exceptions from handlers and logs them safely."""
    error = context.error
    if not error:
        return

    # Specific Telegram error handling
    if isinstance(error, Forbidden):
        logger.warning("Bot was blocked or lacks permission for update: %s", update)
        return

    if isinstance(error, BadRequest):
        logger.warning("Telegram BadRequest error: %s", error)
        return

    if isinstance(error, NetworkError):
        logger.warning("Network connection issue with Telegram servers: %s", error)
        return

    if isinstance(error, Conflict):
        logger.critical("Another instance of the bot is already running! (Conflict error: %s)", error)
        return

    # Log full error with stacktrace for debugging
    logger.error("Uncaught exception while handling an update: %s", error, exc_info=error)

    # Inform user gracefully without leaking stack trace
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Đã xảy ra lỗi không mong muốn trong quá trình xử lý. Vui lòng thử lại sau hoặc liên hệ admin."
            )
        except TelegramError:
            pass
