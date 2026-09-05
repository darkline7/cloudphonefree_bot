"""Async SQLite database connection manager."""

import os
import aiosqlite
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages asynchronous SQLite database connection and table initialization."""

    def __init__(self, db_path: str = "data/bot.db") -> None:
        self.db_path = db_path

    async def init_db(self) -> None:
        """Create necessary tables and indexes if they do not exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")

            # Users table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    referrer_id INTEGER DEFAULT NULL,
                    bonus_turns INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Created accounts history
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS created_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    email TEXT NOT NULL,
                    api_user_id TEXT,
                    trial_received INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                """
            )

            # Pending trial sessions (replaces in-memory pending_trials dictionary)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_sessions (
                    user_id INTEGER PRIMARY KEY,
                    api_user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    cuid TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            # Products table (Shop catalog)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL DEFAULT 0,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Product stock inventory items
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS product_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    is_sold INTEGER DEFAULT 0,
                    order_id INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                );
                """
            )

            # Orders history
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    account_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                """
            )

            # Bank transactions processed (prevent duplicate credits)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    amount INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    transaction_date TEXT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # User balance migrations
            try:
                await db.execute("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0;")
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN total_deposited INTEGER DEFAULT 0;")
            except Exception:
                pass


            # Migrations for existing DB if referrer_id or bonus_turns don't exist
            try:
                await db.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT NULL;")
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN bonus_turns INTEGER DEFAULT 0;")
            except Exception:
                pass

            # Migrate bank_transactions.transaction_id from INTEGER to TEXT if needed
            try:
                # Check current column type
                async with db.execute("PRAGMA table_info(bank_transactions)") as cur:
                    cols = await cur.fetchall()
                    for col in cols:
                        # col: (cid, name, type, notnull, dflt_value, pk)
                        if col[1] == "transaction_id" and col[2].upper() == "INTEGER":
                            # Recreate table with TEXT column
                            await db.execute("""
                                CREATE TABLE IF NOT EXISTS bank_transactions_new (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    transaction_id TEXT UNIQUE NOT NULL,
                                    amount INTEGER NOT NULL,
                                    description TEXT NOT NULL,
                                    transaction_date TEXT,
                                    user_id INTEGER,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                );
                            """)
                            await db.execute("""
                                INSERT OR IGNORE INTO bank_transactions_new
                                    (id, transaction_id, amount, description, transaction_date, user_id, created_at)
                                SELECT id, CAST(transaction_id AS TEXT), amount, description, transaction_date, user_id, created_at
                                FROM bank_transactions;
                            """)
                            await db.execute("DROP TABLE bank_transactions;")
                            await db.execute("ALTER TABLE bank_transactions_new RENAME TO bank_transactions;")
                            logger.info("Migrated bank_transactions.transaction_id from INTEGER to TEXT")
                            break
            except Exception:
                pass


            await db.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    async def get_connection(self) -> aiosqlite.Connection:
        """Return an active connection."""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn
