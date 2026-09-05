"""Asynchronous Database Repositories for Users, Accounts, Sessions, Shop and Bank."""

from typing import Any, Dict, List, Optional
import aiosqlite
from app.database.models import User, CreatedAccount, PendingSession, Product, ProductItem, Order, BankTransaction


class UserRepository:
    """Repository handling telegram user registrations and listings."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def save_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        referrer_id: Optional[int] = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, referrer_id FROM users WHERE user_id = ?", (user_id,)) as cur:
                existing = await cur.fetchone()

            if existing:
                await db.execute(
                    """
                    UPDATE users
                    SET username = COALESCE(?, username),
                        first_name = COALESCE(?, first_name),
                        last_seen_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?;
                    """,
                    (username, first_name, user_id),
                )
            else:
                valid_referrer = referrer_id if (referrer_id and referrer_id != user_id) else None
                await db.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, referrer_id, bonus_turns, created_at, last_seen_at)
                    VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
                    """,
                    (user_id, username, first_name, valid_referrer),
                )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return None
                return User(
                    user_id=row["user_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                    bonus_turns=row["bonus_turns"] if "bonus_turns" in row.keys() else 0,
                    balance=row["balance"] if "balance" in row.keys() else 0,
                    total_deposited=row["total_deposited"] if "total_deposited" in row.keys() else 0,
                    created_at=row["created_at"],
                    last_seen_at=row["last_seen_at"],
                )


    async def add_bonus_turns(self, user_id: int, turns: int = 5) -> None:
        """Add bonus turns to a referrer user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users
                SET bonus_turns = bonus_turns + ?
                WHERE user_id = ?;
                """,
                (turns, user_id),
            )
            await db.commit()

    async def set_bonus_turns(self, user_id: int, turns: int) -> None:
        """Set exact bonus turns for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users
                SET bonus_turns = ?
                WHERE user_id = ?;
                """,
                (turns, user_id),
            )
            await db.commit()

    async def update_balance(self, user_id: int, delta_amount: int) -> int:
        """Add (or deduct if negative) balance for a user. Return new balance."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if delta_amount > 0:
                await db.execute(
                    """
                    UPDATE users
                    SET balance = balance + ?,
                        total_deposited = total_deposited + ?
                    WHERE user_id = ?;
                    """,
                    (delta_amount, delta_amount, user_id),
                )
            else:
                await db.execute(
                    """
                    UPDATE users
                    SET balance = balance + ?
                    WHERE user_id = ?;
                    """,
                    (delta_amount, user_id),
                )
            await db.commit()
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return row["balance"] if row else 0

    async def set_balance(self, user_id: int, balance: int) -> None:
        """Set exact balance for user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET balance = ? WHERE user_id = ?",
                (balance, user_id),
            )
            await db.commit()

    async def delete_user(self, user_id: int) -> None:
        """Delete user and related sessions."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM pending_sessions WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_referrals_count(self, user_id: int) -> int:
        """Count how many users were referred by this user."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def get_all_user_ids(self) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users ORDER BY created_at ASC") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_all_users(self) -> List[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        user_id=row["user_id"],
                        username=row["username"],
                        first_name=row["first_name"],
                        referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                        bonus_turns=row["bonus_turns"] if "bonus_turns" in row.keys() else 0,
                        created_at=row["created_at"],
                        balance=row["balance"] if "balance" in row.keys() else 0,
                        total_deposited=row["total_deposited"] if "total_deposited" in row.keys() else 0,

                        last_seen_at=row["last_seen_at"],
                    )
                    for row in rows
                ]


class AccountRepository:
    """Repository handling generated accounts and statistics."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def get_user_created_count(self, user_id: int) -> int:
        """Count how many accounts a specific user has created."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM created_accounts WHERE user_id = ?",
                (user_id,),
            ) as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def record_created_account(
        self,
        user_id: int,
        username: Optional[str],
        email: str,
        api_user_id: Optional[str] = None,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO created_accounts (user_id, username, email, api_user_id)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, username, email, api_user_id),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Fetch all accounts with user information for web dashboard."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM created_accounts ORDER BY created_at DESC"
            ) as cur:
                rows = await cur.fetchall()
                return [dict(row) for row in rows]

    async def delete_account(self, account_id: int) -> None:
        """Delete an account record by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM created_accounts WHERE id = ?", (account_id,))
            await db.commit()

    async def mark_trial_received(self, user_id: int, email: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE created_accounts
                SET trial_received = 1
                WHERE user_id = ? AND email = ?
                """,
                (user_id, email),
            )
            await db.commit()

    async def get_statistics(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT COUNT(*) AS total FROM created_accounts") as cur:
                row = await cur.fetchone()
                total_count = row["total"] if row else 0

            stats_users: Dict[str, Dict[str, Any]] = {}
            async with db.execute(
                "SELECT user_id, username, email FROM created_accounts ORDER BY id ASC"
            ) as cur:
                rows = await cur.fetchall()
                for r in rows:
                    uid_str = str(r["user_id"])
                    if uid_str not in stats_users:
                        stats_users[uid_str] = {
                            "username": r["username"] or "unknown",
                            "accounts": [],
                        }
                    stats_users[uid_str]["accounts"].append(r["email"])

            return {"total": total_count, "users": stats_users}


class SessionRepository:
    """Repository handling pending trial sessions."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def save_session(self, user_id: int, api_user_id: str, token: str, cuid: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO pending_sessions (user_id, api_user_id, token, cuid, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    api_user_id = excluded.api_user_id,
                    token = excluded.token,
                    cuid = excluded.cuid,
                    created_at = CURRENT_TIMESTAMP;
                """,
                (user_id, api_user_id, token, cuid),
            )
            await db.commit()

    async def get_session(self, user_id: int) -> Optional[PendingSession]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM pending_sessions WHERE user_id = ?",
                (user_id,),
            ) as cur:
                row = await cur.fetchone()
                if not row:
                    return None
                return PendingSession(
                    user_id=row["user_id"],
                    api_user_id=row["api_user_id"],
                    token=row["token"],
                    cuid=row["cuid"],
                    created_at=row["created_at"],
                )

    async def delete_session(self, user_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM pending_sessions WHERE user_id = ?", (user_id,))
            await db.commit()


class ShopRepository:
    """Repository handling shop products, stock items, and user orders."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def get_all_products(self, active_only: bool = False) -> List[Product]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM products"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY id ASC"
            
            async with db.execute(query) as cur:
                rows = await cur.fetchall()
                products = []
                for r in rows:
                    p_id = r["id"]
                    async with db.execute(
                        "SELECT COUNT(*) AS stock FROM product_items WHERE product_id = ? AND is_sold = 0",
                        (p_id,),
                    ) as stock_cur:
                        stock_row = await stock_cur.fetchone()
                        stock = stock_row["stock"] if stock_row else 0

                    products.append(
                        Product(
                            id=p_id,
                            name=r["name"],
                            price=r["price"],
                            description=r["description"],
                            is_active=bool(r["is_active"]),
                            created_at=r["created_at"],
                            stock_count=stock,
                        )
                    )
                return products

    async def get_product(self, product_id: int) -> Optional[Product]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM products WHERE id = ?", (product_id,)) as cur:
                r = await cur.fetchone()
                if not r:
                    return None
                async with db.execute(
                    "SELECT COUNT(*) AS stock FROM product_items WHERE product_id = ? AND is_sold = 0",
                    (product_id,),
                ) as stock_cur:
                    stock_row = await stock_cur.fetchone()
                    stock = stock_row["stock"] if stock_row else 0

                return Product(
                    id=r["id"],
                    name=r["name"],
                    price=r["price"],
                    description=r["description"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                    stock_count=stock,
                )

    async def create_product(self, name: str, price: int, description: Optional[str] = None) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "INSERT INTO products (name, price, description, is_active) VALUES (?, ?, ?, 1)",
                (name, price, description),
            )
            await db.commit()
            return cur.lastrowid

    async def update_product(self, product_id: int, name: str, price: int, description: Optional[str], is_active: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE products SET name = ?, price = ?, description = ?, is_active = ? WHERE id = ?",
                (name, price, description, 1 if is_active else 0, product_id),
            )
            await db.commit()

    async def delete_product(self, product_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM product_items WHERE product_id = ? AND is_sold = 0", (product_id,))
            await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
            await db.commit()

    async def add_stock_items(self, product_id: int, items: List[str]) -> int:
        """Add bulk stock lines to product. Returns count of added items."""
        clean_items = [i.strip() for i in items if i.strip()]
        if not clean_items:
            return 0
        async with aiosqlite.connect(self.db_path) as db:
            for item in clean_items:
                await db.execute(
                    "INSERT INTO product_items (product_id, data, is_sold) VALUES (?, ?, 0)",
                    (product_id, item),
                )
            await db.commit()
        return len(clean_items)

    async def get_stock_items(self, product_id: int, unsold_only: bool = True) -> List[ProductItem]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM product_items WHERE product_id = ?"
            if unsold_only:
                query += " AND is_sold = 0"
            query += " ORDER BY id ASC"
            async with db.execute(query, (product_id,)) as cur:
                rows = await cur.fetchall()
                return [
                    ProductItem(
                        id=r["id"],
                        product_id=r["product_id"],
                        data=r["data"],
                        is_sold=bool(r["is_sold"]),
                        order_id=r["order_id"],
                        created_at=r["created_at"],
                    )
                    for r in rows
                ]

    async def purchase_product(self, user_id: int, username: Optional[str], product_id: int) -> tuple[bool, str, Optional[Order]]:
        """Atomically purchase one stock item of the product. Deduct balance, mark stock as sold, create order."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # 1. Fetch product
            async with db.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)) as p_cur:
                p_row = await p_cur.fetchone()
                if not p_row:
                    return False, "Sản phẩm không tồn tại hoặc đã ngừng bán.", None
                product_name = p_row["name"]
                price = p_row["price"]

            # 2. Check user balance
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as u_cur:
                u_row = await u_cur.fetchone()
                user_balance = u_row["balance"] if u_row else 0
                if user_balance < price:
                    return False, f"Số dư không đủ! (Cần {price:,}đ, hiện có {user_balance:,}đ)", None

            # 3. Get first available stock item
            async with db.execute(
                "SELECT id, data FROM product_items WHERE product_id = ? AND is_sold = 0 ORDER BY id ASC LIMIT 1",
                (product_id,),
            ) as s_cur:
                stock_row = await s_cur.fetchone()
                if not stock_row:
                    return False, "Sản phẩm này tạm thời hết hàng trong kho.", None
                stock_id = stock_row["id"]
                account_data = stock_row["data"]

            # 4. Deduct balance & create order atomically
            await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
            
            order_cur = await db.execute(
                """
                INSERT INTO orders (user_id, username, product_id, product_name, price, account_data)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (user_id, username, product_id, product_name, price, account_data),
            )
            order_id = order_cur.lastrowid

            # 5. Mark stock item sold
            await db.execute(
                "UPDATE product_items SET is_sold = 1, order_id = ? WHERE id = ?",
                (order_id, stock_id),
            )
            await db.commit()
            order = Order(
                id=order_id,
                user_id=user_id,
                username=username,
                product_id=product_id,
                product_name=product_name,
                price=price,
                account_data=account_data,
            )
            return True, "Thành công", order

    async def get_user_orders(self, user_id: int) -> List[Order]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                (user_id,),
            ) as cur:
                rows = await cur.fetchall()
                return [
                    Order(
                        id=r["id"],
                        user_id=r["user_id"],
                        username=r["username"],
                        product_id=r["product_id"],
                        product_name=r["product_name"],
                        price=r["price"],
                        account_data=r["account_data"],
                        created_at=r["created_at"],
                    )
                    for r in rows
                ]

    async def get_all_orders(self) -> List[Order]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders ORDER BY id DESC") as cur:
                rows = await cur.fetchall()
                return [
                    Order(
                        id=r["id"],
                        user_id=r["user_id"],
                        username=r["username"],
                        product_id=r["product_id"],
                        product_name=r["product_name"],
                        price=r["price"],
                        account_data=r["account_data"],
                        created_at=r["created_at"],
                    )
                    for r in rows
                ]


class BankRepository:
    """Repository handling bank transaction records to prevent double processing."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def has_transaction(self, transaction_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT 1 FROM bank_transactions WHERE transaction_id = ?",
                (transaction_id,),
            ) as cur:
                return (await cur.fetchone()) is not None

    async def record_transaction(
        self,
        transaction_id: str,
        amount: int,
        description: str,
        transaction_date: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> bool:
        """Record processed transaction. Returns False if already exists."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """
                    INSERT INTO bank_transactions (transaction_id, amount, description, transaction_date, user_id)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (transaction_id, amount, description, transaction_date, user_id),
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def get_all_transactions(self) -> List[BankTransaction]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM bank_transactions ORDER BY id DESC") as cur:
                rows = await cur.fetchall()
                return [
                    BankTransaction(
                        id=r["id"],
                        transaction_id=r["transaction_id"],
                        amount=r["amount"],
                        description=r["description"],
                        transaction_date=r["transaction_date"],
                        user_id=r["user_id"],
                        created_at=r["created_at"],
                    )
                    for r in rows
                ]


