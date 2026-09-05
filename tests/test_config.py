"""Unit tests for configuration loading and validation."""

import pytest
from app.config import Settings


def test_settings_load_defaults():
    """Test setting default values."""
    s = Settings(BOT_TOKEN="123456789:ABCDefgh-IJKLmnOPqrSTuvWXyz_012345")
    assert s.ENVIRONMENT == "development"
    assert s.LOG_LEVEL == "INFO"
    assert s.CID == "50000"
    assert s.ADMIN_IDS == [7079848501]


def test_settings_admin_ids_parsing():
    """Test parsing of various ADMIN_IDS representations."""
    s1 = Settings(
        BOT_TOKEN="123456789:ABCDefgh-IJKLmnOPqrSTuvWXyz_012345",
        ADMIN_IDS="11111, 22222, 33333",
    )
    assert s1.ADMIN_IDS == [11111, 22222, 33333]


def test_invalid_bot_token():
    """Test validation failure on invalid token format."""
    with pytest.raises(ValueError, match="BOT_TOKEN format is invalid"):
        Settings(BOT_TOKEN="invalid_token_without_colon")

    with pytest.raises(ValueError, match="BOT_TOKEN is not configured"):
        Settings(BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE")
