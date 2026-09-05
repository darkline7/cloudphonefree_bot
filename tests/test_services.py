"""Unit tests for services using unittest.mock."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from app.services.api_client import BaseApiClient
from app.services.mail_service import MailService
from app.services.willclouds_service import WillCloudsService
from app.config import settings


@pytest.mark.asyncio
async def test_mail_service_create_and_read():
    """Test creating temp mail and reading verification code with mocked HTTP responses."""
    mock_client = MagicMock(spec=BaseApiClient)

    # 1. Domains response
    resp_domains = MagicMock(spec=httpx.Response)
    resp_domains.status_code = 200
    resp_domains.json.return_value = {"hydra:member": [{"domain": "tempmail.com"}]}

    # 2. Account response
    resp_account = MagicMock(spec=httpx.Response)
    resp_account.status_code = 201

    # 3. Token response
    resp_token = MagicMock(spec=httpx.Response)
    resp_token.status_code = 200
    resp_token.json.return_value = {"token": "fake_jwt_token"}

    # 4. Messages response
    resp_msgs = MagicMock(spec=httpx.Response)
    resp_msgs.status_code = 200
    resp_msgs.json.return_value = {"hydra:member": [{"id": "msg_1"}]}

    # 5. Message detail response
    resp_msg_detail = MagicMock(spec=httpx.Response)
    resp_msg_detail.status_code = 200
    resp_msg_detail.json.return_value = {"text": "Your verification code is 654321."}

    # Setup side effect
    async def mock_request(method, url, **kwargs):
        if url.endswith("/domains"):
            return resp_domains
        elif url.endswith("/accounts"):
            return resp_account
        elif url.endswith("/token"):
            return resp_token
        elif url.endswith("/messages"):
            return resp_msgs
        elif "/messages/" in url:
            return resp_msg_detail
        return MagicMock(status_code=404)

    mock_client.request = AsyncMock(side_effect=mock_request)

    mail_svc = MailService(mock_client)
    email, password, token = await mail_svc.create_temp_mail()

    assert email.endswith("@tempmail.com")
    assert token == "fake_jwt_token"

    code = await mail_svc.read_code_from_mail(token, timeout=5)
    assert code == "654321"


@pytest.mark.asyncio
async def test_willclouds_service_flow():
    """Test willclouds service api calls with mocked HTTP client."""
    mock_client = MagicMock(spec=BaseApiClient)

    resp_send = MagicMock(spec=httpx.Response)
    resp_send.status_code = 200
    resp_send.json.return_value = {"code": 0, "msg": "ok"}

    resp_login = MagicMock(spec=httpx.Response)
    resp_login.status_code = 200
    resp_login.json.return_value = {"code": 0, "data": {"userId": "99999", "token": "session_tok"}}

    resp_pw = MagicMock(spec=httpx.Response)
    resp_pw.status_code = 200
    resp_pw.json.return_value = {"code": 0, "msg": "ok"}

    resp_trial = MagicMock(spec=httpx.Response)
    resp_trial.status_code = 200
    resp_trial.json.return_value = {"code": 0, "msg": "trial success"}

    async def mock_request(method, url, **kwargs):
        if "send-verification-code" in url:
            return resp_send
        elif "auth/login" in url:
            return resp_login
        elif "set-member-password" in url:
            return resp_pw
        elif "receive-instance" in url:
            return resp_trial
        return MagicMock(status_code=404)

    mock_client.request = AsyncMock(side_effect=mock_request)
    willclouds_svc = WillCloudsService(mock_client, settings)

    # 1. Send verification code
    await willclouds_svc.send_verification_code("user@mail.tm", "cuid123")

    # 2. Login
    uid, tok = await willclouds_svc.login_email_code("user@mail.tm", "654321", "cuid123")
    assert uid == "99999"
    assert tok == "session_tok"

    # 3. Set password
    await willclouds_svc.set_password(uid, tok, "@pass123", "cuid123")

    # 4. Receive trial
    ok, res = await willclouds_svc.receive_trial(uid, tok, "cuid123")
    assert ok is True


@pytest.mark.asyncio
async def test_bank_service_extract_user_id():
    """Test extracting user ID from bank transfer descriptions."""
    from app.services.bank_service import BankService
    from app.database.repositories import BankRepository, UserRepository

    bank_svc = BankService(MagicMock(), MagicMock(), MagicMock(), settings)

    assert bank_svc.extract_user_id("NAP 7079848501 GD 6243MSCBD2DBJ2QV") == 7079848501
    assert bank_svc.extract_user_id("nap 123456789") == 123456789
    assert bank_svc.extract_user_id("NAP:987654321 test") == 987654321
    assert bank_svc.extract_user_id("NAP-555444333") == 555444333
    assert bank_svc.extract_user_id("CK cho ban be") is None


@pytest.mark.asyncio
async def test_bank_service_check_transactions_hex_id():
    """Test bank service correctly processes hex string transaction IDs."""
    from app.services.bank_service import BankService
    from app.database.repositories import BankRepository, UserRepository

    mock_client = MagicMock(spec=BaseApiClient)
    mock_bank_repo = MagicMock(spec=BankRepository)
    mock_user_repo = MagicMock(spec=UserRepository)

    mock_bank_repo.has_transaction = AsyncMock(return_value=False)
    mock_bank_repo.record_transaction = AsyncMock(return_value=True)
    mock_user_repo.update_balance = AsyncMock(return_value=10000)

    # API returns hex string transaction IDs (from modtool ACB API)
    resp_history = MagicMock(spec=httpx.Response)
    resp_history.status_code = 200
    resp_history.json.return_value = {
        "status": "success",
        "transactions": [
            {
                "transactionID": "788560f70c3893a27c424955ce34ee06",
                "amount": 10000,
                "description": "NAP 7079848501 GD 6243MSCBD2DBJ2QV 310826-14:27:04",
                "transactionDate": "31/08/2026 14:27:09",
                "type": "IN",
            },
            {
                "transactionID": "1db1b22baf8ea9a0109faa056144bc71",
                "amount": 60000,
                "description": "CK ngoai",
                "transactionDate": "29/08/2026 16:32:38",
                "type": "OUT",
            },
        ],
    }

    mock_client.request = AsyncMock(return_value=resp_history)

    bank_svc = BankService(mock_client, mock_bank_repo, mock_user_repo, settings)
    processed = await bank_svc.check_transactions()

    assert processed == 1
    mock_bank_repo.has_transaction.assert_called_once_with("788560f70c3893a27c424955ce34ee06")
    mock_bank_repo.record_transaction.assert_called_once_with(
        transaction_id="788560f70c3893a27c424955ce34ee06",
        amount=10000,
        description="NAP 7079848501 GD 6243MSCBD2DBJ2QV 310826-14:27:04",
        transaction_date="31/08/2026 14:27:09",
        user_id=7079848501,
    )
    mock_user_repo.update_balance.assert_called_once_with(user_id=7079848501, delta_amount=10000)

