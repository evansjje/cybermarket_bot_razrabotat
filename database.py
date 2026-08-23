# database.py
import aiosqlite
import os
from typing import List, Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "cybermarket.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Initialize database tables and seed demo data."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            await db.commit()

            # Seed demo data if empty
            await self._seed_demo_data(db)

    async def _seed_demo_data(self, db: aiosqlite.Connection) -> None:
        """Seed demo categories and products if database is empty."""
        cursor = await db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count == 0:
            demo_categories = [
                ("🎮 Игры", "Цифровые игры для PC и консолей"),
                ("💻 Софт", "Лицензионное программное обеспечение"),
                ("🎁 Подарки", "Подарочные карты и сертификаты"),
            ]
            await db.executemany(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                demo_categories,
            )
            await db.commit()

            cursor = await db.execute("SELECT id FROM categories")
            cat_ids = [row[0] for row in await cursor.fetchall()]

            demo_products = [
                (cat_ids[0], "Cyberpunk 2077", "Цифровая версия игры для PC", 1999.0, 10),
                (cat_ids[0], "Elden Ring", "Цифровая версия игры для PC", 2499.0, 8),
                (cat_ids[1], "Windows 11 Pro", "Лицензионный ключ активации", 2999.0, 20),
                (cat_ids[2], "Steam Gift Card 1000₽", "Подарочная карта Steam", 1000.0, 15),
            ]
            await db.executemany(
                """INSERT INTO products (category_id, name, description, price, stock)
                   VALUES (?, ?, ?, ?, ?)""",
                demo_products,
            )
            await db.commit()

    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str, referral_code: str = None, referred_by: int = None) -> None:
        """Register a new user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR IGNORE INTO users (id, username, first_name, last_name, referral_code, referred_by)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, username, first_name, last_name, referral_code, referred_by),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM categories ORDER BY id")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Get products by category ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM products WHERE category_id = ? AND stock > 0",
                (category_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        """Add product to user's cart."""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if product already in cart
            cursor = await db.execute(
                "SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
            existing = await cursor.fetchone()
            if existing:
                await db.execute(
                    "UPDATE cart SET quantity = quantity + ? WHERE id = ?",
                    (quantity, existing[0]),
                )
            else:
                await db.execute(
                    "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                    (user_id, product_id, quantity),
                )
            await db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart with product details."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT c.id as cart_id, c.quantity, p.id as product_id, p.name, p.price, p.description
                   FROM cart c
                   JOIN products p ON c.product_id = p.id
                   WHERE c.user_id = ?""",
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def remove_from_cart(self, cart_id: int) -> None:
        """Remove item from cart."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
            await db.commit()

    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            await db.commit()

    async def create_order(self, user_id: int, items: List[Dict[str, Any]]) -> int:
        """Create order from cart items. Returns order ID."""
        total = sum(item["price"] * item["quantity"] for item in items)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO orders (user_id, total_amount) VALUES (?, ?)",
                (user_id, total),
            )
            order_id = cursor.lastrowid

            for item in items:
                await db.execute(
                    """INSERT INTO order_items (order_id, product_id, quantity, price)
                       VALUES (?, ?, ?, ?)""",
                    (order_id, item["product_id"], item["quantity"], item["price"]),
                )
                # Decrease stock
                await db.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (item["quantity"], item["product_id"]),
                )

            await db.commit()
            return order_id

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_order_items(self, order_id: int) -> List[Dict[str, Any]]:
        """Get items of an order."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT oi.*, p.name
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.id
                   WHERE oi.order_id = ?""",
                (order_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        """Get admin statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            users_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM orders")
            orders_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM products")
            products_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM categories")
            categories_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT SUM(total_amount) FROM orders")
            revenue = (await cursor.fetchone())[0] or 0

            return {
                "users": users_count,
                "orders": orders_count,
                "products": products_count,
                "categories": categories_count,
                "revenue": revenue,
            }

    async def add_product(self, category_id: int, name: str, description: str, price: float, stock: int) -> None:
        """Add new product."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO products (category_id, name, description, price, stock)
                   VALUES (?, ?, ?, ?, ?)""",
                (category_id, name, description, price, stock),
            )
            await db.commit()

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products ORDER BY id")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_referral_stats(self, user_id: int) -> Dict[str, int]:
        """Get referral statistics for user."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE referred_by = ?",
                (user_id,),
            )
            referrals_count = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT referral_code FROM users WHERE id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            referral_code = row[0] if row else None

            return {"count": referrals_count, "code": referral_code}


db = Database()
