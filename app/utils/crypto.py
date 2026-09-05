"""Cryptographic utilities: Java URLEncode, MD5 Signature, RSA Encryption."""

import base64
import hashlib
from typing import Any, Dict, Tuple
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


def java_url_encode(s: Any) -> str:
    """
    Emulate Java's URLEncoder.encode behavior.
    - Spaces become '+'
    - Alphanumerics and '-._*' remain unescaped
    - Other characters become uppercase '%XX'
    """
    bs = str(s).encode("utf-8")
    out = []
    for b in bs:
        if b == 32:  # ' '
            out.append("+")
        elif (
            (48 <= b <= 57)   # 0-9
            or (65 <= b <= 90)   # A-Z
            or (97 <= b <= 122)  # a-z
            or b in (45, 46, 95, 42)  # -, ., _, *
        ):
            out.append(chr(b))
        else:
            out.append("%" + format(b, "02X"))
    return "".join(out)


def query_string(obj: Dict[str, Any]) -> str:
    """Build a sorted, URL-encoded query string from a dictionary."""
    return "&".join(
        [
            f"{java_url_encode(k)}={java_url_encode(str(obj[k]))}"
            for k in sorted(obj.keys())
        ]
    )


def sign_payload(obj: Dict[str, Any], salt: str) -> Tuple[str, str]:
    """
    Calculate MD5 signature for API payload using specified salt.
    Returns (x_signature, encoded_body).
    """
    encoded_body = query_string(obj)
    full_str = encoded_body + salt
    md5_hash = hashlib.md5(full_str.encode("utf-8")).hexdigest()
    x_signature = md5_hash[4:20]
    return x_signature, encoded_body


def rsa_encrypt(data: str, public_key_pem: str) -> str:
    """
    Encrypt string data with RSA public key using PKCS#1 v1.5 padding,
    returning base64 encoded string.
    """
    clean_key = public_key_pem.replace("\\n", "\n").strip()
    key = RSA.import_key(clean_key)
    cipher = PKCS1_v1_5.new(key)
    encrypted_bytes = cipher.encrypt(data.encode("utf-8"))
    return base64.b64encode(encrypted_bytes).decode("utf-8")
