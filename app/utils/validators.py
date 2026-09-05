"""Input validation utilities."""

import re


def validate_email(email: str) -> bool:
    """Validate standard email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_broadcast_content(content: str) -> str:
    """Validate and clean broadcast content."""
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("Nội dung thông báo không được để trống.")
    if len(cleaned) > 4000:
        raise ValueError("Nội dung thông báo quá dài (tối đa 4000 ký tự).")
    return cleaned
