import aiosqlite
from typing import List, Dict, Optional, Union


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._init_tables()
        await self._seed_data()

    async def _init_tables(self):
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT DEFAULT '',
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.commit()

    async def _seed_data(self):
        # Check if categories are empty
        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = [
                ("🎮 Игры",),
                ("💻 Софт",),
                ("🎁 Подарки",)
            ]
            await self.db.executemany("INSERT INTO categories (title) VALUES (?)", categories)
            await self.db.commit()

            # Get category IDs
            cursor = await self.db.execute("SELECT id FROM categories")
            cat_ids = [row[0] for row in await cursor.fetchall()]

            products = [
                (cat_ids[0], "CS2 Prime", "Аккаунт с Prime статусом", 1499.0),
                (cat_ids[0], "Steam Wallet 1000", "Пополнение кошелька Steam", 1200.0),
                (cat_ids[1], "Windows 11 Pro", "Лицензионный ключ", 2999.0),
                (cat_ids[2], "Discord Nitro 1 мес", "Подарочная подписка", 499.0)
            ]
            await self.db.executemany(
                "INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)",
                products
            )
            await self.db.commit()

    async def get_categories(self) -> List[Dict]:
        cursor = await self.db.execute("SELECT * FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        cursor = await self.db.execute("INSERT INTO categories (title) VALUES (?)", (title,))
        await self.db.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict]:
        if category_id:
            cursor = await self.db.execute(
                "SELECT * FROM products WHERE category_id = ? ORDER BY id",
                (category_id,)
            )
        else:
            cursor = await self.db.execute("SELECT * FROM products ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        cursor = await self.db.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        cursor = await self.db.execute(
            "INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)",
            (category_id, title, desc, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float):
        await self.db.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (price, product_id)
        )
        await self.db.commit()

    async def update_product_desc(self, product_id: int, desc: str):
        await self.db.execute(
            "UPDATE products SET desc = ? WHERE id = ?",
            (desc, product_id)
        )
        await self.db.commit()

    async def delete_product(self, product_id: int):
        await self.db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self.db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await self.db.commit()

    async def add_to_cart(self, user_id: int, product_id: int):
        # Check if product already in cart
        cursor = await self.db.execute(
            "SELECT id, count FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        row = await cursor.fetchone()
        if row:
            await self.db.execute(
                "UPDATE cart SET count = count + 1 WHERE id = ?",
                (row["id"],)
            )
        else:
            await self.db.execute(
                "INSERT INTO cart (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id)
            )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict]:
        cursor = await self.db.execute("""
            SELECT p.id, p.title, p.price, c.count
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.id
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int):
        await self.db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict:
        cursor = await self.db.execute("SELECT COUNT(*) FROM users")
        users = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM cart")
        orders = (await cursor.fetchone())[0]

        return {
            'users': users,
            'orders': orders,
            'revenue': 0
        }

    async def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        await self.db.execute("""
            INSERT OR IGNORE INTO users (id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        await self.db.commit()

    async def close(self):
        if self.db:
            await self.db.close()


# Singleton instance
db = Database()
