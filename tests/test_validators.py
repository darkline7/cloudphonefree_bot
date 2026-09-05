"""Unit tests for validators and helpers."""

import pytest
from app.utils.validators import validate_email, validate_broadcast_content
from app.utils.helpers import escape_html, format_account_stats


def test_validate_email():
    """Test valid and invalid email addresses."""
    assert validate_email("test@example.com") is True
    assert validate_email("user.name+tag@sub.domain.org") is True
    assert validate_email("invalid_email") is False
    assert validate_email("@domain.com") is False


def test_validate_broadcast_content():
    """Test broadcast text validator."""
    assert validate_broadcast_content("  Hello Admin  ") == "Hello Admin"
    with pytest.raises(ValueError, match="không được để trống"):
        validate_broadcast_content("   ")


def test_escape_html():
    """Test HTML escaping."""
    raw = "<script>alert('xss')</script> & \"hello\""
    escaped = escape_html(raw)
    assert "<script>" not in escaped
    assert "&lt;script&gt;" in escaped
    assert "&amp;" in escaped


def test_format_account_stats():
    """Test formatting account stats output."""
    sample_stats = {
        "total": 2,
        "users": {
            "123": {
                "username": "tester",
                "accounts": ["acc1@mail.tm", "acc2@mail.tm"],
            }
        },
    }
    output = format_account_stats(sample_stats)
    assert "Tổng tài khoản đã tạo:</b> 2" in output
    assert "@tester" in output
    assert "acc1@mail.tm" in output


@pytest.mark.asyncio
async def test_is_user_member_of_chat():
    """Test is_user_member_of_chat helper."""
    from unittest.mock import AsyncMock, MagicMock
    from app.utils.helpers import is_user_member_of_chat

    bot_mock = MagicMock()
    member_mock = MagicMock()
    member_mock.status = "member"
    bot_mock.get_chat_member = AsyncMock(return_value=member_mock)

    assert await is_user_member_of_chat(bot_mock, 12345, -1003804934789) is True

    member_mock.status = "left"
    assert await is_user_member_of_chat(bot_mock, 12345, -1003804934789) is False

    bot_mock.get_chat_member = AsyncMock(side_effect=Exception("Chat not found"))
    assert await is_user_member_of_chat(bot_mock, 12345, -1003804934789) is False

@pytest.mark.asyncio
async def test_referral_and_account_quota_flow(tmp_path):
    """Test referral registration, account quota limits, and bonus turns."""
    from app.database.connection import DatabaseManager
    from app.database.repositories import UserRepository, AccountRepository

    db_path = str(tmp_path / "test_ref.db")
    db_mgr = DatabaseManager(db_path)
    await db_mgr.init_db()

    user_repo = UserRepository(db_path)
    account_repo = AccountRepository(db_path)

    # 1. User 100 registers
    await user_repo.save_user(user_id=100, username="user_a", first_name="User A")
    u100 = await user_repo.get_user(100)
    assert u100 is not None
    assert u100.bonus_turns == 0
    assert await account_repo.get_user_created_count(100) == 0

    # 2. User 200 registers using User 100's referral link
    await user_repo.save_user(user_id=200, username="user_b", first_name="User B", referrer_id=100)
    u200 = await user_repo.get_user(200)
    assert u200.referrer_id == 100

    # Referral count of User 100 should be 1
    assert await user_repo.get_referrals_count(100) == 1

    # User 200 creates their 1st account -> triggers +5 bonus turns for User 100
    await account_repo.record_created_account(user_id=200, username="user_b", email="b1@mail.tm")
    await user_repo.add_bonus_turns(100, turns=5)

    # Check User 100 bonus turns: now has +5 turns (can create 10 + 5 = 15 accounts total)
    u100_updated = await user_repo.get_user(100)
    assert u100_updated.bonus_turns == 5

    # User 100 creates 15 accounts
    for i in range(15):
        await account_repo.record_created_account(user_id=100, username="user_a", email=f"a{i}@mail.tm")

    u100_created = await account_repo.get_user_created_count(100)
    assert u100_created == 15




@pytest.mark.asyncio
async def test_shop_and_bank_integration(tmp_path):
    """Test Shop purchase flow and Bank deposit processing."""
    from app.database.connection import DatabaseManager
    from app.database.repositories import UserRepository, ShopRepository, BankRepository
    from app.services.bank_service import BankService
    from app.config import Settings

    db_path = str(tmp_path / "test_shop.db")
    db_mgr = DatabaseManager(db_path=db_path)
    await db_mgr.init_db()

    user_repo = UserRepository(db_path=db_path)
    shop_repo = ShopRepository(db_path=db_path)
    bank_repo = BankRepository(db_path=db_path)

    # 1. Register user
    await user_repo.save_user(user_id=12345, username="buyer1", first_name="Buyer")
    user = await user_repo.get_user(12345)
    assert user.balance == 0

    # 2. Deposit money to user balance
    # 2. Deposit money to user balance
    await user_repo.update_balance(user_id=12345, delta_amount=50000)
    user = await user_repo.get_user(12345)
    assert user.balance == 50000

    # 3. Create shop product and add stock
    p_id = await shop_repo.create_product(name="UmoCloud 6H VIP", price=20000, description="Test product")
    added = await shop_repo.add_stock_items(product_id=p_id, items=["acc1@umo.com|pass1", "acc2@umo.com|pass2"])
    assert added == 2

    prod = await shop_repo.get_product(p_id)
    assert prod.stock_count == 2

    # 4. Buy product
    ok, msg, order = await shop_repo.purchase_product(user_id=12345, username="buyer1", product_id=p_id)
    assert ok is True
    assert order is not None
    assert order.account_data == "acc1@umo.com|pass1"
    assert order.price == 20000

    # Verify balance reduced
    user = await user_repo.get_user(12345)
    assert user.balance == 30000

    # Verify stock reduced
    prod = await shop_repo.get_product(p_id)
    assert prod.stock_count == 1

    # 5. Test bank memo parsing and duplicate transaction handling
    test_settings = Settings(
        BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ123456789",
        WEB_USERNAME="admin",
        WEB_PASSWORD="password",
        SECRET_KEY="secret_key_long_enough_for_session",
        ACB_API_TOKEN="acb_token",
        BANK_ACCOUNT_NO="2345678",
        BANK_ACCOUNT_NAME="NGUYEN VAN A",
        BANK_MEMO_PREFIX="NAP",
    )

    bank_service = BankService(
        api_client=None, # Mock not needed for extract_memo_user_id / generate_vietqr_url
        bank_repo=bank_repo,
        user_repo=user_repo,
        settings=test_settings,
    )

    extracted_id = bank_service.extract_user_id("MBVCB.12345.NAP 12345 thanh toan")
    assert extracted_id == 12345

    qr_url = bank_service.generate_vietqr_url(user_id=12345, amount=50000)
    assert "2345678" in qr_url
    assert "NAP" in qr_url and "12345" in qr_url
