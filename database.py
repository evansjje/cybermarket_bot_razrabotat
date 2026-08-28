# database.py
import aiosqlite
from typing import List, Optional, Dict, Any


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Establish database connection and initialize schema."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def _create_tables(self) -> None:
        """Create all necessary tables if they don't exist."""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT DEFAULT '',
                price REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.commit()

    async def _seed_data(self) -> None:
        """Populate database with initial categories and products."""
        # Check if categories exist
        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = [
                ("🎮 Игры",),
                ("💻 ПО",),
                ("🎁 Подарки",)
            ]
            await self.db.executemany(
                "INSERT INTO categories (title) VALUES (?)", categories
            )
            await self.db.commit()

            # Get category IDs
            cursor = await self.db.execute("SELECT id FROM categories")
            cat_ids = [row[0] for row in await cursor.fetchall()]

            products = [
                (cat_ids[0], "Steam Gift Card $50", "Цифровая карта пополнения Steam на $50", 3500),
                (cat_ids[0], "Xbox Game Pass Ultimate 1 месяц", "Подписка Xbox Game Pass Ultimate на 1 месяц", 1200),
                (cat_ids[1], "Windows 11 Pro Key", "Лицензионный ключ активации Windows 11 Pro", 1500),
                (cat_ids[2], "Discord Nitro 1 месяц", "Подписка Discord Nitro на 1 месяц", 800),
            ]
            await self.db.executemany(
                """INSERT INTO products (category_id, title, desc, price) 
                   VALUES (?, ?, ?, ?)""",
                products
            )
            await self.db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        cursor = await self.db.execute("SELECT * FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        """Add a new category and return its ID."""
        cursor = await self.db.execute(
            "INSERT INTO categories (title) VALUES (?)", (title,)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get products, optionally filtered by category."""
        if category_id is not None:
            cursor = await self.db.execute(
                "SELECT * FROM products WHERE category_id = ? ORDER BY id",
                (category_id,)
            )
        else:
            cursor = await self.db.execute("SELECT * FROM products ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        """Add a new product and return its ID."""
        cursor = await self.db.execute(
            """INSERT INTO products (category_id, title, desc, price) 
               VALUES (?, ?, ?, ?)""",
            (category_id, title, desc, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float) -> None:
        """Update product price."""
        await self.db.execute(
            "UPDATE products SET price = ? WHERE id = ?", (price, product_id)
        )
        await self.db.commit()

    async def update_product_desc(self, product_id: int, desc: str) -> None:
        """Update product description."""
        await self.db.execute(
            "UPDATE products SET desc = ? WHERE id = ?", (desc, product_id)
        )
        await self.db.commit()

    async def delete_product(self, product_id: int) -> None:
        """Delete a product and its cart entries."""
        await self.db.execute(
            "DELETE FROM cart WHERE product_id = ?", (product_id,)
        )
        await self.db.execute(
            "DELETE FROM products WHERE id = ?", (product_id,)
        )
        await self.db.commit()

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        """Add a product to user's cart."""
        cursor = await self.db.execute(
            """SELECT id, count FROM cart 
               WHERE user_id = ? AND product_id = ?""",
            (user_id, product_id)
        )
        row = await cursor.fetchone()
        if row:
            await self.db.execute(
                "UPDATE cart SET count = count + 1 WHERE id = ?", (row["id"],)
            )
        else:
            await self.db.execute(
                """INSERT INTO cart (user_id, product_id, count) 
                   VALUES (?, ?, 1)""",
                (user_id, product_id)
            )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart with product details."""
        cursor = await self.db.execute(
            """SELECT p.id, p.title, p.price, c.count 
               FROM cart c 
               JOIN products p ON c.product_id = p.id 
               WHERE c.user_id = ?""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart."""
        await self.db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics for admin panel."""
        cursor = await self.db.execute("SELECT COUNT(*) FROM users")
        users_count = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM products")
        products_count = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        categories_count = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM cart")
        cart_items = (await cursor.fetchone())[0]

        return {
            "users": users_count,
            "products": products_count,
            "categories": categories_count,
            "cart_items": cart_items
        }

    async def register_user(self, user_id: int, username: str = None, 
                           first_name: str = None, last_name: str = None) -> None:
        """Register a new user or update existing."""
        await self.db.execute(
            """INSERT OR REPLACE INTO users (user_id, username, first_name, last_name) 
               VALUES (?, ?, ?, ?)""",
            (user_id, username, first_name, last_name)
        )
        await self.db.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self.db:
            await self.db.close()


# Global database instance
db = Database()
