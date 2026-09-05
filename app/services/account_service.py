"""Account creation and trial orchestration service."""

import logging
import uuid
from typing import Callable, Coroutine, Optional, Tuple
from app.config import Settings
from app.services.mail_service import MailService
from app.services.willclouds_service import WillCloudsService

logger = logging.getLogger(__name__)


class AccountService:
    """Orchestrates account registration lifecycle between MailService and WillCloudsService."""

    def __init__(
        self,
        mail_service: MailService,
        willclouds_service: WillCloudsService,
        settings: Settings,
    ) -> None:
        self.mail_service = mail_service
        self.willclouds_service = willclouds_service
        self.settings = settings

    async def create_account(
        self,
        progress_callback: Optional[Callable[[str], Coroutine]] = None,
    ) -> Tuple[str, str, str, str, str]:
        """
        Full workflow:
        1. Generate temp mail
        2. Send OTP code via WillClouds
        3. Poll OTP code from mailbox
        4. Login to WillClouds
        5. Set fixed password
        Returns (email, fixed_password, api_user_id, token, cuid).
        """
        cuid = str(uuid.uuid4()).replace("-", "")

        # Step 1: Create temp email
        if progress_callback:
            await progress_callback("📡 Tạo email tạm...")
        email, _, mail_token = await self.mail_service.create_temp_mail()

        # Step 2: Send verification code
        if progress_callback:
            await progress_callback("📨 Gửi mã xác minh...")
        await self.willclouds_service.send_verification_code(email, cuid)

        # Step 3: Wait for OTP
        if progress_callback:
            await progress_callback("📬 Chờ nhận mã...")
        code = await self.mail_service.read_code_from_mail(
            mail_token,
            timeout=self.settings.MAIL_POLL_TIMEOUT,
        )

        # Step 4: Login
        api_user_id, token = await self.willclouds_service.login_email_code(email, code, cuid)

        # Step 5: Set password
        await self.willclouds_service.set_password(
            api_user_id,
            token,
            self.settings.FIXED_PASSWORD,
            cuid,
        )

        logger.info("Successfully created account for email: %s, user_id: %s", email, api_user_id)
        return email, self.settings.FIXED_PASSWORD, api_user_id, token, cuid
