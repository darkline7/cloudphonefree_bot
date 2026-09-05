"""Application configuration module using Pydantic Settings."""

import re
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token from @BotFather")
    ADMIN_IDS: List[int] = Field(
        default_factory=lambda: [7079848501],
        description="List of Telegram User IDs with admin privileges",
    )
    # Required Channel/Group to Join
    REQUIRED_CHAT_ID: int = Field(
        default=-1003804934789,
        description="Required Telegram channel/group ID users must join",
    )
    REQUIRED_CHAT_URL: str = Field(
        default="https://t.me/+fHk_70X0X0xkZTM1",
        description="Invite link for the required Telegram channel/group",
    )

    # Auto Bank ACB Configuration (https://api.modtool.fun/historyapiacbv2/{token})
    BANK_API_TOKEN: str = Field(default="", description="Token for ACB Auto Bank API modtool.fun")
    BANK_API_URL: str = Field(
        default="https://api.modtool.fun/historyapiacbv2/{token}",
        description="ACB API endpoint template",
    )
    BANK_NAME: str = Field(default="ACB", description="Bank Name (e.g. ACB, MB, VietinBank)")
    BANK_ACCOUNT_NO: str = Field(default="", description="Bank Account Number for QR deposit")
    BANK_ACCOUNT_NAME: str = Field(default="", description="Bank Account Owner Name")
    BANK_MEMO_PREFIX: str = Field(default="NAP", description="Memo prefix for user deposit (e.g. NAP)")
    BANK_CHECK_INTERVAL: int = Field(default=20, description="Interval in seconds for bank polling")
    VIETQR_BANK_BIN: str = Field(default="970416", description="VietQR Bank BIN (ACB is 970416)")


    # Application & Environment
    ENVIRONMENT: str = Field(default="development", description="Current environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    DATABASE_PATH: str = Field(
        default="data/bot.db",
        description="Path to SQLite database file",
    )

    # WillClouds / UmoCloud API Configurations
    CID: str = Field(default="50000", description="Client ID")
    CVER: str = Field(default="10010016", description="Client Version")
    LOCALE: str = Field(default="en-US", description="Locale")
    CLIENT_TYPE: str = Field(default="h5", description="Client Type")
    SALT: str = Field(
        default="4d9cbb6b585448419578a95954a2b886",
        description="MD5 Signature Salt",
    )
    TENANT_ID: str = Field(default="242", description="Tenant ID")
    BRAND_ID: str = Field(default="108", description="Brand ID")
    CHANNEL: str = Field(default="h5_cphone", description="Channel")
    FIXED_PASSWORD: str = Field(
        default="@thanhbinhdev",
        description="Default password set for new accounts",
    )
    PUBLIC_KEY: str = Field(
        default="""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbHF73B6NPGm5lwS4hVGg+W8VO
ezCt+Af4Cvx7UZjXakyk7U6QgPABK4JNnlRTV0wgySMM5zv9H9qXL6ltbqskKeZd
DXhWaqu9oytBCaBg4nEA5O/y44qnm+NI+Tu35ulGDzSfQxP2js9LV3bcqjv/hP0S
9aj2jBKINUKE2swiGQIDAQAB
-----END PUBLIC KEY-----""",
        description="RSA Public Key for password encryption",
    )

    # Timeouts & Limits
    API_TIMEOUT: int = Field(default=30, description="HTTP Request Timeout in seconds")
    MAIL_POLL_TIMEOUT: int = Field(
        default=120,
        description="Max wait time for OTP email in seconds",
    )
    COOLDOWN_SECONDS: int = Field(
        default=10,
        description="Cooldown time between user actions in seconds",
    )

    # Web Dashboard Settings
    WEB_HOST: str = Field(default="127.0.0.1", description="Web Dashboard Host")
    WEB_PORT: int = Field(default=8000, description="Web Dashboard Port")
    WEB_USERNAME: str = Field(default="admin", description="Web Admin Username")
    WEB_PASSWORD: str = Field(default="admin123", description="Web Admin Password")
    SECRET_KEY: str = Field(default="super-secret-web-key-change-me", description="Session Secret Key")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """Parse comma-separated string or list of admin IDs."""
        if isinstance(v, str):
            ids = [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
            return ids if ids else [7079848501]
        elif isinstance(v, int):
            return [v]
        elif isinstance(v, list):
            return [int(i) for i in v]
        return [7079848501]

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate Telegram bot token format."""
        v = v.strip()
        if not v or v == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            raise ValueError(
                "BOT_TOKEN is not configured! Please provide a valid token in .env file."
            )
        # Check standard Telegram bot token pattern: <number>:<string>
        if not re.match(r"^\d+:[A-Za-z0-9_-]+$", v):
            raise ValueError("BOT_TOKEN format is invalid. Expected format: 123456789:ABCDefgh...")
        return v

    @property
    def formatted_public_key(self) -> str:
        """Ensure clean PEM format for RSA public key."""
        clean_key = self.PUBLIC_KEY.replace("\\n", "\n").strip()
        return clean_key


# Singleton instance
settings = Settings()
