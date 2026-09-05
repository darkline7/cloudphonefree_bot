"""Application Dependency Injection Container."""

from app.config import Settings, settings
from app.database.connection import DatabaseManager
from app.database.repositories import (
    AccountRepository,
    BankRepository,
    SessionRepository,
    ShopRepository,
    UserRepository,
)
from app.middlewares.rate_limit import RateLimiter
from app.services.account_service import AccountService
from app.services.api_client import BaseApiClient
from app.services.bank_service import BankService
from app.services.mail_service import MailService
from app.services.willclouds_service import WillCloudsService


class Container:
    """Dependency container holding all application singletons."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings

        # Database & Repositories
        self.db_manager = DatabaseManager(db_path=self.settings.DATABASE_PATH)
        self.user_repo = UserRepository(db_path=self.settings.DATABASE_PATH)
        self.account_repo = AccountRepository(db_path=self.settings.DATABASE_PATH)
        self.session_repo = SessionRepository(db_path=self.settings.DATABASE_PATH)
        self.shop_repo = ShopRepository(db_path=self.settings.DATABASE_PATH)
        self.bank_repo = BankRepository(db_path=self.settings.DATABASE_PATH)

        # HTTP Client & Services
        self.api_client = BaseApiClient(timeout=float(self.settings.API_TIMEOUT))
        self.mail_service = MailService(api_client=self.api_client)
        self.willclouds_service = WillCloudsService(
            api_client=self.api_client,
            settings=self.settings,
        )
        self.account_service = AccountService(
            mail_service=self.mail_service,
            willclouds_service=self.willclouds_service,
            settings=self.settings,
        )
        self.bank_service = BankService(
            api_client=self.api_client,
            bank_repo=self.bank_repo,
            user_repo=self.user_repo,
            settings=self.settings,
        )

        # Middleware
        self.rate_limiter = RateLimiter(cooldown_seconds=self.settings.COOLDOWN_SECONDS)

    async def init(self) -> None:
        """Initialize async resources (database tables, etc.)."""
        await self.db_manager.init_db()

    async def close(self) -> None:
        """Close open network connections and database pools."""
        await self.bank_service.stop_polling()
        await self.api_client.close()


# Global container instance
container = Container()

