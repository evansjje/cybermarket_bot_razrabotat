import aiosqlite
from typing import List, Dict, Any

DB_PATH = "cybermarket.db"


async def init_db() -> None:
    """Initialize database and create tables if not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                price REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        await seed_data()


async def seed_data() -> None:
    """Seed default categories and products if empty."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Check if categories exist
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM categories")
        row = await cursor.fetchone()
        if row["cnt"] > 0:
            return

        categories = [
            ("🎮 Игры",),
            ("💻 Софт",),
            ("🎁 Подарки",)
        ]
        await db.executemany("INSERT INTO categories (name) VALUES (?)", categories)
        await db.commit()

        # Get category ids
        cursor = await db.execute("SELECT id, name FROM categories")
        cat_rows = await cursor.fetchall()
        cat_map = {r["name"]: r["id"] for r in cat_rows}

        products = [
            (cat_map["🎮 Игры"], "Steam Gift Card 10$", "Цифровая карта пополнения Steam на 10$", 850),
            (cat_map["🎮 Игры"], "Xbox Game Pass Ultimate 1 месяц", "Подписка Xbox Game Pass Ultimate на 1 месяц", 1200),
            (cat_map["💻 Софт"], "Windows 11 Pro ключ", "Лицензионный ключ активации Windows 11 Pro", 1500),
            (cat_map["💻 Софт"], "Office 2021 ключ", "Лицензионный ключ активации Microsoft Office 2021", 2000),
            (cat_map["🎁 Подарки"], "VK Coin 1000", "Виртуальная валюта VK Coin 1000 штук", 500),
            (cat_map["🎁 Подарки"], "Telegram Premium 1 месяц", "Подписка Telegram Premium на 1 месяц", 800),
        ]
        await db.executemany(
            "INSERT INTO products (category_id, title, description, price) VALUES (?, ?, ?, ?)",
            products
        )
        await db.commit()


async def get_categories() -> List[Dict[str, Any]]:
    """Get all categories."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, name FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_products(category_id: int) -> List[Dict[str, Any]]:
    """Get products by category."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, category_id, title, description, price FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_product_by_id(product_id: int) -> Dict[str, Any] | None:
    """Get single product by id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, category_id, title, description, price FROM products WHERE id = ?",
            (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_to_cart(user_id: int, product_id: int, count: int = 1) -> None:
    """Add product to cart or increment count."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Check if already in cart
        cursor = await db.execute(
            "SELECT id, count FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE cart SET count = count + ? WHERE id = ?",
                (count, row["id"])
            )
        else:
            await db.execute(
                "INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, ?)",
                (user_id, product_id, count)
            )
        await db.commit()


async def get_cart(user_id: int) -> List[Dict[str, Any]]:
    """Get user's cart with product details."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT c.id, c.product_id, c.count, p.title, p.price, p.description
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.id
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def clear_cart(user_id: int) -> None:
    """Clear user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


async def delete_product(product_id: int) -> None:
    """Delete product by id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await db.commit()


async def update_product_price(product_id: int, price: float) -> None:
    """Update product price."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
        await db.commit()


async def update_product_desc(product_id: int, desc: str) -> None:
    """Update product description."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE products SET description = ? WHERE id = ?", (desc, product_id))
        await db.commit()


async def get_stats() -> Dict[str, Any]:
    """Get bot statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        row = await cursor.fetchone()
        users_count = row["cnt"] if row else 0
        return {
            "users": users_count,
            "orders": 0,
            "revenue": 0
        }


async def add_user(user_id: int, username: str | None, first_name: str | None, last_name: str | None) -> None:
    """Add or update user in database."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        await db.commit()
