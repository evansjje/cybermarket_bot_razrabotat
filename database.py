import aiosqlite
import os

DB_PATH = "cybermarket.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def _create_tables(self):
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER,
                product_id INTEGER,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                count INTEGER,
                total_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        await self.db.commit()

    async def _seed_data(self):
        # Check if categories exist
        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = [
                ("🎮 Игры",),
                ("💻 Софт",),
                ("🎁 Подарки",),
            ]
            await self.db.executemany("INSERT INTO categories (name) VALUES (?)", categories)
            await self.db.commit()

        # Check if products exist
        cursor = await self.db.execute("SELECT COUNT(*) FROM products")
        count = (await cursor.fetchone())[0]
        if count == 0:
            products = [
                (1, "Steam Gift Card $50", "Пополнение кошелька Steam на $50", 3500.0),
                (1, "Xbox Game Pass Ultimate 1 месяц", "Подписка на 1 месяц", 999.0),
                (2, "Windows 10 Pro ключ", "Лицензионный ключ активации", 1500.0),
                (3, "VK Coin 1000", "Виртуальная валюта VK", 100.0),
            ]
            await self.db.executemany(
                "INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)",
                products,
            )
            await self.db.commit()

    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referrer_id: int = None):
        await self.db.execute(
            "INSERT OR IGNORE INTO users (id, username, first_name, last_name, referrer_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, referrer_id),
        )
        await self.db.commit()

    async def get_categories(self) -> list:
        cursor = await self.db.execute("SELECT * FROM categories")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_products(self, category_id: int = None) -> list:
        if category_id:
            cursor = await self.db.execute("SELECT * FROM products WHERE category_id = ?", (category_id,))
        else:
            cursor = await self.db.execute("SELECT * FROM products")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> dict:
        cursor = await self.db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_to_cart(self, user_id: int, product_id: int):
        await self.db.execute(
            """
            INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, 1)
            ON CONFLICT(user_id, product_id) DO UPDATE SET count = count + 1
            """,
            (user_id, product_id),
        )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> list:
        cursor = await self.db.execute(
            """
            SELECT p.*, c.count FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int):
        await self.db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def delete_product(self, product_id: int):
        await self.db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self.db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await self.db.commit()

    async def get_stats(self) -> dict:
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM users")
        users = (await cursor.fetchone())["cnt"]

        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM orders")
        orders = (await cursor.fetchone())["cnt"]

        cursor = await self.db.execute("SELECT COALESCE(SUM(total_price), 0) as revenue FROM orders")
        revenue = (await cursor.fetchone())["revenue"]

        return {"users": users, "orders": orders, "revenue": revenue}

    async def get_referrals_count(self, user_id: int) -> int:
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM users WHERE referrer_id = ?", (user_id,))
        return (await cursor.fetchone())["cnt"]

    async def create_order(self, user_id: int, product_id: int, count: int, total_price: float):
        await self.db.execute(
            "INSERT INTO orders (user_id, product_id, count, total_price) VALUES (?, ?, ?, ?)",
            (user_id, product_id, count, total_price),
        )
        await self.db.commit()

    async def close(self):
        if self.db:
            await self.db.close()


db = Database()
