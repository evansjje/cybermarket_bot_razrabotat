# database.py
import aiosqlite
from typing import List, Dict, Any, Optional


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self._init_db()
        await self._seed_data()

    async def _init_db(self):
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT DEFAULT '',
                price REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.commit()

    async def _seed_data(self):
        # Проверяем, есть ли категории
        cursor = await self.conn.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = ["Электроника", "Софт", "Игры"]
            for cat in categories:
                await self.add_category(cat)

            # Добавляем товары
            products = [
                (1, "iPhone 15 Pro", "Новейший смартфон Apple", 999.99),
                (1, "Samsung Galaxy S24", "Флагман Samsung", 899.99),
                (2, "Windows 11 Pro", "Лицензионная ОС", 199.99),
                (3, "Cyberpunk 2077", "Игра года", 59.99),
            ]
            for cat_id, title, desc, price in products:
                await self.add_product(cat_id, title, desc, price)

    async def get_categories(self) -> List[Dict[str, Any]]:
        cursor = await self.conn.execute("SELECT * FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        cursor = await self.conn.execute(
            "INSERT INTO categories (title) VALUES (?)", (title,)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if category_id is not None:
            cursor = await self.conn.execute(
                "SELECT * FROM products WHERE category_id = ? ORDER BY id", (category_id,)
            )
        else:
            cursor = await self.conn.execute("SELECT * FROM products ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        cursor = await self.conn.execute(
            "INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)",
            (category_id, title, desc, price),
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float):
        await self.conn.execute(
            "UPDATE products SET price = ? WHERE id = ?", (price, product_id)
        )
        await self.conn.commit()

    async def update_product_desc(self, product_id: int, desc: str):
        await self.conn.execute(
            "UPDATE products SET desc = ? WHERE id = ?", (desc, product_id)
        )
        await self.conn.commit()

    async def delete_product(self, product_id: int):
        await self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self.conn.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await self.conn.commit()

    async def add_to_cart(self, user_id: int, product_id: int):
        # Проверяем, есть ли уже такой товар в корзине
        cursor = await self.conn.execute(
            "SELECT * FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        existing = await cursor.fetchone()
        if existing:
            await self.conn.execute(
                "UPDATE cart SET count = count + 1 WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
        else:
            await self.conn.execute(
                "INSERT INTO cart (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id),
            )
        await self.conn.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = await self.conn.execute(
            """
            SELECT p.id, p.title, p.price, c.count
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int):
        await self.conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def get_stats(self) -> Dict[str, Any]:
        # Общая статистика
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
        users_count = (await cursor.fetchone())[0]

        cursor = await self.conn.execute("SELECT COUNT(*) FROM products")
        products_count = (await cursor.fetchone())[0]

        cursor = await self.conn.execute("SELECT COUNT(*) FROM categories")
        categories_count = (await cursor.fetchone())[0]

        cursor = await self.conn.execute("SELECT COUNT(*) FROM cart")
        cart_items = (await cursor.fetchone())[0]

        return {
            "users": users_count,
            "products": products_count,
            "categories": categories_count,
            "cart_items": cart_items,
        }

    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        await self.conn.execute(
            """
            INSERT OR IGNORE INTO users (id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, first_name, last_name),
        )
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()


db = Database()
