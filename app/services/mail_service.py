"""Mail.tm temporary email service integration."""

import asyncio
import logging
import random
import re
import string
import time
from typing import Tuple
from app.services.api_client import BaseApiClient

logger = logging.getLogger(__name__)


class MailService:
    """Handles temporary email generation and OTP retrieval from mail.tm."""

    BASE_URL = "https://api.mail.tm"

    def __init__(self, api_client: BaseApiClient) -> None:
        self.client = api_client

    async def create_temp_mail(self) -> Tuple[str, str, str]:
        """
        Create a temporary email address on mail.tm.
        Returns (email_address, password, auth_token).
        """
        headers = {"User-Agent": "Mozilla/5.0"}

        # 1. Get available domains
        r_domains = await self.client.request(
            "GET",
            f"{self.BASE_URL}/domains",
            headers=headers,
        )
        if r_domains.status_code != 200:
            raise RuntimeError(f"Không thể lấy danh sách domain mail.tm (HTTP {r_domains.status_code})")

        domain_data = r_domains.json()
        members = domain_data.get("hydra:member", [])
        if not members:
            raise RuntimeError("Không tìm thấy domain mail.tm khả dụng.")
        domain = members[0]["domain"]

        # 2. Generate random credentials
        username = "".join(random.choices(string.ascii_lowercase, k=8))
        email = f"{username}@{domain}"
        password = "".join(random.choices(string.ascii_letters + string.digits, k=12))

        payload = {"address": email, "password": password}

        # 3. Create account
        r_account = await self.client.request(
            "POST",
            f"{self.BASE_URL}/accounts",
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
        )
        if r_account.status_code not in (200, 201):
            raise RuntimeError(f"Tạo tài khoản email tạm thất bại (HTTP {r_account.status_code}): {r_account.text}")

        # 4. Obtain bearer token
        r_token = await self.client.request(
            "POST",
            f"{self.BASE_URL}/token",
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
        )
        if r_token.status_code != 200:
            raise RuntimeError(f"Lấy token email tạm thất bại (HTTP {r_token.status_code}): {r_token.text}")

        token = r_token.json().get("token")
        if not token:
            raise RuntimeError("Không nhận được token từ mail.tm.")

        logger.info("Created temp email: %s", email)
        return email, password, token

    async def read_code_from_mail(self, token: str, timeout: int = 120) -> str:
        """
        Poll inbox for incoming email and extract 6-digit OTP code.
        Non-blocking async loop with sleep interval.
        """
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0",
        }

        while time.time() - start_time < timeout:
            await asyncio.sleep(3.0)
            try:
                r_messages = await self.client.request(
                    "GET",
                    f"{self.BASE_URL}/messages",
                    headers=headers,
                )
                if r_messages.status_code != 200:
                    continue

                messages = r_messages.json().get("hydra:member", [])
                if not messages:
                    continue

                # Get latest message
                msg_id = messages[0]["id"]
                r_msg_detail = await self.client.request(
                    "GET",
                    f"{self.BASE_URL}/messages/{msg_id}",
                    headers=headers,
                )
                if r_msg_detail.status_code != 200:
                    continue

                data = r_msg_detail.json()
                text = data.get("text") or data.get("intro") or ""
                codes = re.findall(r"\b\d{6}\b", text)
                if codes:
                    logger.info("Found OTP verification code from mail.")
                    return codes[0]
            except Exception as e:
                logger.debug("Error while polling mail.tm: %s", e)
                continue

        raise TimeoutError("Hết thời gian chờ mã xác minh, vui lòng thử lại sau.")
