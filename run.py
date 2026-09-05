"""Entry point for running CloudPhone Free Telegram Bot and Web Dashboard concurrently."""

import asyncio
import logging
import sys
import uvicorn
from app.config import settings
from app.logging_config import setup_logging
from app.main import build_application, on_shutdown, on_startup
from app.web import web_app


async def run_services():
    """Run both the Telegram Bot and FastAPI Web Dashboard concurrently in the same event loop."""
    logger = logging.getLogger(__name__)

    # Build Telegram Bot application
    bot_app = build_application()

    # Configure Uvicorn Server for Web Dashboard
    config = uvicorn.Config(
        app=web_app,
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False,
    )
    server = uvicorn.Server(config)

    logger.info("Initializing Telegram Bot and Database...")
    await bot_app.initialize()
    await on_startup(bot_app)
    await bot_app.updater.start_polling(drop_pending_updates=True)
    await bot_app.start()

    logger.info(f"🚀 Web Dashboard is running at http://{settings.WEB_HOST}:{settings.WEB_PORT}")
    logger.info("🤖 Telegram Bot is running and polling updates...")

    try:
        # Run Web Server while Bot is polling
        await server.serve()
    finally:
        logger.info("Stopping Telegram Bot and services...")
        if bot_app.updater and bot_app.updater.running:
            await bot_app.updater.stop()
        if bot_app.running:
            await bot_app.stop()
        await on_shutdown(bot_app)
        await bot_app.shutdown()
        logger.info("All services shut down cleanly.")


def main() -> None:
    """Entry point."""
    logger = setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file_path="logs/bot.log",
    )
    logger.info(
        "Starting CloudPhone Free Telegram Bot & Web Dashboard (Environment: %s)...",
        settings.ENVIRONMENT,
    )

    try:
        asyncio.run(run_services())
    except KeyboardInterrupt:
        logger.info("Received termination signal (Ctrl+C). Exiting...")
    except Exception as e:
        logger.critical("Fatal error encountered during execution: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

