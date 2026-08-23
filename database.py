# database.py
import aiosqlite
from typing import Optional

DB_PATH = "cybermarket.db"


async def init_db() -> None:
    """Initialize database and create tables if not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
                desc TEXT,
                price REAL NOT NULL,
                file_data TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                total_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id),
                FOREIGN KEY (referred_id) REFERENCES users (id)
            )
        """)
        await db.commit()

        # Seed demo data
        await seed_demo_data(db)


async def seed_demo_data(db: aiosqlite.Connection) -> None:
    """Insert demo categories and products if database is empty."""
    # Check if categories table is empty
    cursor = await db.execute("SELECT COUNT(*) FROM categories")
    count = (await cursor.fetchone())[0]
    if count > 0:
        return

    # Insert demo categories
    categories = [
        ("Скрипты",),
        ("Курсы",),
        ("Софт",)
    ]
    await db.executemany("INSERT INTO categories (name) VALUES (?)", categories)
    await db.commit()

    # Get category IDs
    cursor = await db.execute("SELECT id, name FROM categories")
    cat_ids = {name: cid for cid, name in await cursor.fetchall()}

    # Insert demo products
    products = [
        (cat_ids["Скрипты"], "Автопостинг для Telegram", "Скрипт для автоматического постинга в Telegram-каналы. Поддержка расписания и множества аккаунтов.", 499.0, "demo_script_1.txt"),
        (cat_ids["Скрипты"], "Парсер товаров с Wildberries", "Мощный парсер для сбора данных о товарах с Wildberries. Экспорт в Excel/CSV.", 799.0, "demo_script_2.txt"),
        (cat_ids["Курсы"], "Python для начинающих", "Полный курс по Python с нуля до продвинутого уровня. 50+ часов видео, домашние задания.", 1999.0, "demo_course_1.pdf"),
        (cat_ids["Софт"], "VPN-клиент Pro", "Быстрый и стабильный VPN-клиент с неограниченным трафиком. Поддержка всех платформ.", 299.0, "demo_soft_1.exe")
    ]
    await db.executemany(
        "INSERT INTO products (category_id, title, desc, price, file_data) VALUES (?, ?, ?, ?, ?)",
        products
    )
    await db.commit()


# --- User functions ---
async def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> None:
    """Add new user to database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[tuple]:
    """Get user by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return await cursor.fetchone()


async def count_users() -> int:
    """Get total number of users."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]


# --- Category functions ---
async def get_categories() -> list[tuple]:
    """Get all categories."""
    return await get_all_categories()


async def get_all_categories() -> list[tuple]:
    """Get all categories."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name FROM categories ORDER BY id")
        return await cursor.fetchall()


async def get_category(category_id: int) -> Optional[tuple]:
    """Get category by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        return await cursor.fetchone()


# --- Product functions ---
async def get_products_by_category(category_id: int) -> list[tuple]:
    """Get all products in a category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, desc, price FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        return await cursor.fetchall()


async def get_product(product_id: int) -> Optional[tuple]:
    """Get product by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return await cursor.fetchone()


async def add_product(category_id: int, title: str, desc: str, price: float, file_data: str = None) -> int:
    """Add new product. Returns product ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO products (category_id, title, desc, price, file_data) VALUES (?, ?, ?, ?, ?)",
            (category_id, title, desc, price, file_data)
        )
        await db.commit()
        return cursor.lastrowid


async def delete_product(product_id: int) -> None:
    """Delete product by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


# --- Cart functions ---
async def add_to_cart(user_id: int, product_id: int, count: int = 1) -> None:
    """Add product to user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if item already in cart
        cursor = await db.execute(
            "SELECT count FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        if existing:
            await db.execute(
                "UPDATE cart SET count = count + ? WHERE user_id = ? AND product_id = ?",
                (count, user_id, product_id)
            )
        else:
            await db.execute(
                "INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, ?)",
                (user_id, product_id, count)
            )
        await db.commit()


async def get_cart(user_id: int) -> list[tuple]:
    """Get user's cart with product details."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT p.id, p.title, p.price, c.count, (p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY p.id
        """, (user_id,))
        return await cursor.fetchall()


async def get_cart_items(user_id: int) -> list[tuple]:
    """Get user's cart items with product details."""
    return await get_cart(user_id)


async def update_cart_item(user_id: int, product_id: int, count: int) -> None:
    """Update cart item count."""
    async with aiosqlite.connect(DB_PATH) as db:
        if count <= 0:
            await db.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
        else:
            await db.execute(
                "UPDATE cart SET count = ? WHERE user_id = ? AND product_id = ?",
                (count, user_id, product_id)
            )
        await db.commit()


async def clear_cart(user_id: int) -> None:
    """Clear user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_cart_total(user_id: int) -> float:
    """Get total price of user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT SUM(p.price * c.count)
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        result = await cursor.fetchone()
        return result[0] if result[0] else 0.0


# --- Order functions ---
async def create_order(user_id: int, product_id: int, count: int, total_price: float) -> int:
    """Create new order. Returns order ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, product_id, count, total_price) VALUES (?, ?, ?, ?)",
            (user_id, product_id, count, total_price)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_orders(user_id: int) -> list[tuple]:
    """Get all orders for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT o.id, p.title, o.count, o.total_price, o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
        return await cursor.fetchall()


async def get_all_orders() -> list[tuple]:
    """Get all orders."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT o.id, u.username, u.first_name, u.last_name, p.title, o.count, o.total_price, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
        """)
        return await cursor.fetchall()


async def count_orders() -> int:
    """Get total number of orders."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        return (await cursor.fetchone())[0]


async def get_all_orders_count() -> int:
    """Get total number of orders."""
    return await count_orders()


async def get_all_users_count() -> int:
    """Get total number of users."""
    return await count_users()


# --- Review functions ---
async def add_review(user_id: int, product_id: int, rating: int, comment: str = None) -> None:
    """Add a review for a product."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?, ?, ?, ?)",
            (user_id, product_id, rating, comment)
        )
        await db.commit()


async def get_reviews(product_id: int) -> list[tuple]:
    """Get all reviews for a product."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT r.id, u.username, r.rating, r.comment, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
        """, (product_id,))
        return await cursor.fetchall()


# --- Referral functions ---
async def add_referral(referrer_id: int, referred_id: int) -> None:
    """Add a referral relationship."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, referred_id)
        )
        await db.commit()


async def get_referrals_count(user_id: int) -> int:
    """Get count of referrals for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
            (user_id,)
        )
        return (await cursor.fetchone())[0]


# --- Database class wrapper ---
class Database:
    """Database wrapper class for synchronous access patterns."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    async def __aenter__(self):
        self.conn = await aiosqlite.connect(self.db_path)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()
    
    async def get_user(self, user_id: int) -> Optional[tuple]:
        """Get user by ID."""
        cursor = await self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return await cursor.fetchone()
    
    async def get_categories(self) -> list[tuple]:
        """Get all categories."""
        return await self.get_all_categories()
    
    async def get_all_categories(self) -> list[tuple]:
        """Get all categories."""
        cursor = await self.conn.execute("SELECT id, name FROM categories ORDER BY id")
        return await cursor.fetchall()
    
    async def get_products_by_category(self, category_id: int) -> list[tuple]:
        """Get all products in a category."""
        cursor = await self.conn.execute(
            "SELECT id, title, desc, price FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        return await cursor.fetchall()
    
    async def get_product(self, product_id: int) -> Optional[tuple]:
        """Get product by ID."""
        cursor = await self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return await cursor.fetchone()
    
    async def get_cart(self, user_id: int) -> list[tuple]:
        """Get user's cart with product details."""
        cursor = await self.conn.execute("""
            SELECT p.id, p.title, p.price, c.count, (p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY p.id
        """, (user_id,))
        return await cursor.fetchall()
    
    async def get_user_orders(self, user_id: int) -> list[tuple]:
        """Get all orders for a user."""
        cursor = await self.conn.execute("""
            SELECT o.id, p.title, o.count, o.total_price, o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
        return await cursor.fetchall()
    
    async def get_all_orders(self) -> list[tuple]:
        """Get all orders."""
        cursor = await self.conn.execute("""
            SELECT o.id, u.username, u.first_name, u.last_name, p.title, o.count, o.total_price, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
        """)
        return await cursor.fetchall()
    
    async def get_reviews(self, product_id: int) -> list[tuple]:
        """Get all reviews for a product."""
        cursor = await self.conn.execute("""
            SELECT r.id, u.username, r.rating, r.comment, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
        """, (product_id,))
        return await cursor.fetchall()
    
    async def get_cart_items(self, user_id: int) -> list[tuple]:
        """Get user's cart items."""
        return await self.get_cart(user_id)
    
    async def count_users(self) -> int:
        """Get total number of users."""
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]
    
    async def count_orders(self) -> int:
        """Get total number of orders."""
        cursor = await self.conn.execute("SELECT COUNT(*) FROM orders")
        return (await cursor.fetchone())[0]
    
    async def get_all_orders_count(self) -> int:
        """Get total number of orders."""
        return await self.count_orders()
    
    async def get_all_users_count(self) -> int:
        """Get total number of users."""
        return await self.count_users()
    
    async def get_referrals_count(self, user_id: int) -> int:
        """Get count of referrals for a user."""
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
            (user_id,)
        )
        return (await cursor.fetchone())[0]
