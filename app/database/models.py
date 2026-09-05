"""Data models for database entities."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    created_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    referrer_id: Optional[int] = None
    bonus_turns: int = 0
    balance: int = 0
    total_deposited: int = 0


@dataclass
class Product:
    id: Optional[int]
    name: str
    price: int
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    stock_count: int = 0


@dataclass
class ProductItem:
    id: Optional[int]
    product_id: int
    data: str  # Account data e.g. email|pass or token
    is_sold: bool = False
    order_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class Order:
    id: Optional[int]
    user_id: int
    username: Optional[str]
    product_id: int
    product_name: str
    price: int
    account_data: str
    created_at: Optional[str] = None


@dataclass
class BankTransaction:
    id: Optional[int]
    transaction_id: str
    amount: int
    description: str
    transaction_date: Optional[str]
    user_id: Optional[int] = None
    created_at: Optional[str] = None



@dataclass
class CreatedAccount:
    id: Optional[int]
    user_id: int
    username: Optional[str]
    email: str
    api_user_id: Optional[str] = None
    trial_received: bool = False
    created_at: Optional[str] = None


@dataclass
class PendingSession:
    user_id: int
    api_user_id: str
    token: str
    cuid: str
    created_at: Optional[str] = None
