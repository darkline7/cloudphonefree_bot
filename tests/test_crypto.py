"""Unit tests for cryptographic and encoding functions."""

from app.utils.crypto import java_url_encode, query_string, sign_payload, rsa_encrypt
from app.config import settings


def test_java_url_encode():
    """Test java url encode behavior vs Java standard."""
    assert java_url_encode("hello world") == "hello+world"
    assert java_url_encode("test@123_-. *") == "test%40123_-.+*"


def test_query_string():
    """Test query string sorting and concatenation."""
    data = {"b": "2", "a": "1", "c": "hello world"}
    qs = query_string(data)
    assert qs == "a=1&b=2&c=hello+world"


def test_sign_payload():
    """Test MD5 signature computation."""
    data = {"cid": "50000", "cver": "10010016"}
    sig, body = sign_payload(data, salt="test_salt")
    assert isinstance(sig, str)
    assert len(sig) == 16
    assert "cid=50000&cver=10010016" == body


def test_rsa_encrypt():
    """Test RSA public key encryption."""
    encrypted = rsa_encrypt("my_password", settings.formatted_public_key)
    assert isinstance(encrypted, str)
    assert len(encrypted) > 20
