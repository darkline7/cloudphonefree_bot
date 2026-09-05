"""Auto Bank Polling and VietQR Generator Service."""

import asyncio
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional
from telegram import Bot
from app.config import Settings
from app.database.repositories import BankRepository, UserRepository
from app.services.api_client import BaseApiClient

logger = logging.getLogger(__name__)


class BankService:
    """Service to poll ACB bank transactions via modtool.fun API and process deposits."""

    def __init__(
        self,
        api_client: BaseApiClient,
        bank_repo: BankRepository,
        user_repo: UserRepository,
        settings: Settings,
    ) -> None:
        self.api_client = api_client
        self.bank_repo = bank_repo
        self.user_repo = user_repo
        self.settings = settings
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._bot: Optional[Bot] = None
        self._lock = asyncio.Lock()  # Prevent concurrent check_transactions overlap

    def set_bot(self, bot: Bot) -> None:
        """Set active Telegram bot instance for sending deposit notifications."""
        self._bot = bot

    def generate_vietqr_url(self, user_id: int, amount: int = 0) -> str:
        """Generate VietQR quick-pay image URL for bank transfer."""
        bin_code = self.settings.VIETQR_BANK_BIN or "970416"
        account_no = self.settings.BANK_ACCOUNT_NO or ""
        memo = f"{self.settings.BANK_MEMO_PREFIX} {user_id}"
        account_name = self.settings.BANK_ACCOUNT_NAME or ""
        
        url = f"https://img.vietqr.io/image/{bin_code}-{account_no}-compact2.png"
        params = []
        if amount > 0:
            params.append(f"amount={amount}")
        if memo:
            params.append(f"addInfo={urllib.parse.quote(memo)}")
        if account_name:
            params.append(f"accountName={urllib.parse.quote(account_name)}")
            
        if params:
            url += "?" + "&".join(params)
        return url

    async def fetch_bank_history(self) -> List[Dict[str, Any]]:
        """Fetch bank transactions from modtool ACB API."""
        token = self.settings.BANK_API_TOKEN
        if not token:
            return []

        url = self.settings.BANK_API_URL.replace("{token}", token)
        try:
            resp = await self.api_client.request("GET", url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success" and isinstance(data.get("transactions"), list):
                    return data.get("transactions", [])
            else:
                logger.warning("Bank API returned status %d: %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Error fetching bank history: %s", e)
        return []

    def extract_user_id(self, description: str) -> Optional[int]:
        """Extract user_id from transfer description (e.g. 'NAP 123456789' or 'NAP123456789')."""
        prefix = re.escape(self.settings.BANK_MEMO_PREFIX)
        pattern = rf"{prefix}\s*[:\-_]?\s*(\d+)"
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    async def check_transactions(self) -> int:
        """Check and process newly incoming transactions. Return count of processed deposits.

        Uses an asyncio.Lock so that overlapping calls (auto-poller + manual
        'check_deposit' button) never credit the same transaction twice.
        """
        async with self._lock:
            transactions = await self.fetch_bank_history()
            if not transactions:
                return 0

            processed_count = 0
            for tx in transactions:
                tx_type = tx.get("type", "").upper()
                if tx_type != "IN":
                    continue

                tx_id = str(tx.get("transactionID", "")).strip()
                if not tx_id:
                    continue

                already_done = await self.bank_repo.has_transaction(tx_id)
                if already_done:
                    continue

                try:
                    amount = int(tx.get("amount", 0))
                except (ValueError, TypeError):
                    continue

                description = tx.get("description", "")
                tx_date = tx.get("transactionDate", "")

                if amount <= 0:
                    continue

                user_id = self.extract_user_id(description)

                recorded = await self.bank_repo.record_transaction(
                    transaction_id=tx_id,
                    amount=amount,
                    description=description,
                    transaction_date=tx_date,
                    user_id=user_id,
                )

                if not recorded:
                    continue

                processed_count += 1

                if user_id:
                    new_balance = await self.user_repo.update_balance(user_id=user_id, delta_amount=amount)
                    logger.info(
                        "Deposit credited: User %s +%d VND | TxID: %s | New Balance: %d VND",
                        user_id, amount, tx_id, new_balance
                    )

                    if self._bot:
                        try:
                            msg = (
                                "🎉 <b>NẠP TIỀN THÀNH CÔNG!</b>\n\n"
                                f"💵 <b>Số tiền nạp:</b> <code>+{amount:,}đ</code>\n"
                                f"💰 <b>Số dư hiện tại:</b> <code>{new_balance:,}đ</code>\n"
                                f"🔖 <b>Mã giao dịch:</b> <code>#{tx_id[:16]}...</code>\n"
                                f"📅 <b>Thời gian:</b> <code>{tx_date}</code>\n\n"
                                "Cảm ơn bạn đã ủng hộ dịch vụ! Bạn có thể vào <b>Cửa Hàng</b> để mua tài khoản ngay bây giờ."
                            )
                            await self._bot.send_message(chat_id=user_id, text=msg, parse_mode="HTML")
                        except Exception as e:
                            logger.warning("Failed to send deposit notification to user %s: %s", user_id, e)
                else:
                    logger.info("Processed Bank TxID %s (%d VND) without matching user memo: %s", tx_id, amount, description)

            return processed_count

    async def start_polling(self) -> None:
        """Start background polling task."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Bank Auto Polling service started.")

    async def stop_polling(self) -> None:
        """Stop background polling task."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Bank Auto Polling service stopped.")

    async def _poll_loop(self) -> None:
        """Infinite loop polling bank API."""
        while self._is_running:
            try:
                if self.settings.BANK_API_TOKEN:
                    await self.check_transactions()
            except Exception as e:
                logger.error("Error in bank polling loop: %s", e)
            
            interval = max(5, self.settings.BANK_CHECK_INTERVAL)
            await asyncio.sleep(interval)

