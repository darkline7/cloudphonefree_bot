"""WillClouds / UmoCloud API client implementation."""

import logging
import time
from typing import Any, Dict, Tuple
from app.config import Settings
from app.services.api_client import BaseApiClient
from app.utils.crypto import rsa_encrypt, sign_payload

logger = logging.getLogger(__name__)


class WillCloudsService:
    """Handles communication with WillClouds/UmoCloud SaaS APIs."""

    def __init__(self, api_client: BaseApiClient, settings: Settings) -> None:
        self.client = api_client
        self.settings = settings

    def _make_headers(self, token: str = "", content_type: bool = False) -> Dict[str, str]:
        """Construct standard HTTP headers required by WillClouds API."""
        h = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": self.settings.LOCALE,
            "Origin": "https://h5.willclouds.com",
            "Referer": "https://h5.willclouds.com/",
            "tenant-id": self.settings.TENANT_ID,
            "client-brand-id": self.settings.BRAND_ID,
            "timezone": "Asia/Saigon",
        }
        if token:
            h["Authorization"] = f"Bearer {token}"
        if content_type:
            h["Content-Type"] = "application/x-www-form-urlencoded"
        return h

    async def send_verification_code(self, email: str, cuid: str) -> None:
        """Request verification OTP code sent to specified email."""
        data = {
            "cuid": cuid,
            "ts": str(int(time.time() * 1000)),
            "userId": "",
            "cid": self.settings.CID,
            "chnl": self.settings.CHANNEL,
            "cver": self.settings.CVER,
            "locale": self.settings.LOCALE,
            "clientType": self.settings.CLIENT_TYPE,
            "scene": "1",
            "captcha": "",
            "account": email,
            "accountType": "mail",
        }
        sig, body = sign_payload(data, self.settings.SALT)
        headers = self._make_headers(content_type=True)
        headers["x-signature"] = sig

        url = "https://oem-api.willclouds.com/saas-api/cloud-client/auth/send-verification-code"
        r = await self.client.request("POST", url, data=body, headers=headers)
        res = r.json()
        if res.get("code") != 0:
            raise RuntimeError(f"Gửi mã xác minh thất bại: {r.text}")

    async def login_email_code(self, email: str, code: str, cuid: str) -> Tuple[str, str]:
        """Login using email and OTP verification code. Returns (user_id, token)."""
        data = {
            "cuid": cuid,
            "ts": str(int(time.time() * 1000)),
            "userId": "",
            "cid": self.settings.CID,
            "chnl": self.settings.CHANNEL,
            "cver": self.settings.CVER,
            "locale": self.settings.LOCALE,
            "clientType": self.settings.CLIENT_TYPE,
            "account": email,
            "loginType": "MAIL_CODE",
            "authContent": code,
        }
        sig, body = sign_payload(data, self.settings.SALT)
        headers = self._make_headers(content_type=True)
        headers["x-signature"] = sig

        url = "https://oem-core.willclouds.com/saas-api/cloud-client/auth/login"
        r = await self.client.request("POST", url, data=body, headers=headers)
        res = r.json()
        if res.get("code") != 0:
            raise RuntimeError(f"Đăng nhập thất bại: {r.text}")

        user_id = str(res["data"]["userId"])
        token = str(res["data"]["token"])
        return user_id, token

    async def set_password(self, user_id: str, token: str, password: str, cuid: str) -> None:
        """Encrypt password with RSA public key and set member password."""
        enc_pw = rsa_encrypt(password, self.settings.formatted_public_key)
        data = {
            "cuid": cuid,
            "ts": str(int(time.time() * 1000)),
            "userId": str(user_id),
            "cid": self.settings.CID,
            "chnl": self.settings.CHANNEL,
            "cver": self.settings.CVER,
            "locale": self.settings.LOCALE,
            "clientType": self.settings.CLIENT_TYPE,
            "password": enc_pw,
        }
        sig, body = sign_payload(data, self.settings.SALT)
        headers = self._make_headers(token=token, content_type=True)
        headers["x-signature"] = sig

        url = "https://oem-core.willclouds.com/saas-api/cloud-client/user/set-member-password"
        r = await self.client.request("POST", url, data=body, headers=headers)
        res = r.json()
        if res.get("code") != 0:
            raise RuntimeError(f"Đặt mật khẩu thất bại: {r.text}")

    async def receive_trial(self, user_id: str, token: str, cuid: str) -> Tuple[bool, Dict[str, Any]]:
        """Claim 6-hour trial cloud phone instance."""
        data = {
            "cuid": cuid,
            "ts": str(int(time.time() * 1000)),
            "userId": str(user_id),
            "cid": self.settings.CID,
            "chnl": self.settings.CHANNEL,
            "cver": self.settings.CVER,
            "locale": self.settings.LOCALE,
            "clientType": self.settings.CLIENT_TYPE,
        }
        sig, body = sign_payload(data, self.settings.SALT)
        headers = self._make_headers(token=token, content_type=True)
        headers["x-signature"] = sig

        url = "https://oem-api.willclouds.com/saas-api/cloud-client/user/receive-instance"
        r = await self.client.request("POST", url, data=body, headers=headers)
        res = r.json()
        success = res.get("code") == 0
        return success, res
