# database.py
import aiosqlite
from typing import List, Dict, Optional, Any
from datetime import datetime

DB_PATH = "cybermarket.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Initialize database tables and seed demo data"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create tables
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registered_at TEXT,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
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
                    added_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    items TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            await db.commit()
            
            # Seed demo data if empty
            await self._seed_demo_data(db)

    async def _seed_demo_data(self, db: aiosqlite.Connection) -> None:
        """Seed demo categories and products on first run"""
        # Check if categories table is empty
        cursor = await db.execute("SELECT COUNT(*) FROM categories")
        count = await cursor.fetchone()
        
        if count[0] == 0:
            # Demo categories
            categories = [
                ("🎮 Игры", "Цифровые игры для PC и консолей"),
                ("💻 Софт", "Лицензионное программное обеспечение"),
                ("🎁 Подарки", "Подарочные карты и сертификаты"),
            ]
            
            for name, desc in categories:
                await db.execute(
                    "INSERT INTO categories (name, description) VALUES (?, ?)",
                    (name, desc)
                )
            
            # Demo products
            products = [
                (1, "Cyberpunk 2077", "Цифровая версия игры для PC (GOG)", 1999.0, 50),
                (1, "Elden Ring", "Цифровая версия игры для PC (Steam)", 2499.0, 30),
                (2, "Windows 11 Pro", "Лицензионный ключ активации", 1499.0, 100),
                (3, "Steam Gift Card 1000₽", "Подарочная карта Steam на 1000 рублей", 950.0, 200),
            ]
            
            for cat_id, name, desc, price, stock in products:
                await db.execute(
                    "INSERT INTO products (category_id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
                    (cat_id, name, desc, price, stock)
                )
            
            await db.commit()

    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str, referred_by: Optional[int] = None) -> None:
        """Register a new user"""
        async with aiosqlite.connect(self.db_path) as db:
            referral_code = f"REF{user_id}"
            await db.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name, registered_at, referral_code, referred_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username, first_name, last_name, datetime.now().isoformat(), referral_code, referred_by)
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM categories")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get products, optionally filtered by category"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if category_id:
                cursor = await db.execute("SELECT * FROM products WHERE category_id = ?", (category_id,))
            else:
                cursor = await db.execute("SELECT * FROM products")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get single product by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        """Add product to user's cart"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if item already in cart
            cursor = await db.execute(
                "SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
            existing = await cursor.fetchone()
            
            if existing:
                await db.execute(
                    "UPDATE cart SET quantity = quantity + ? WHERE id = ?",
                    (quantity, existing[0])
                )
            else:
                await db.execute(
                    "INSERT INTO cart (user_id, product_id, quantity, added_at) VALUES (?, ?, ?, ?)",
                    (user_id, product_id, quantity, datetime.now().isoformat())
                )
            await db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart with product details"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT c.id as cart_id, c.quantity, p.*, 
                       (p.price * c.quantity) as total_price
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
                ORDER BY c.added_at DESC
            """, (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def remove_from_cart(self, cart_id: int) -> None:
        """Remove item from cart"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
            await db.commit()

    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            await db.commit()

    async def create_order(self, user_id: int, items: List[Dict[str, Any]], total_amount: float) -> int:
        """Create new order and return order ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO orders (user_id, total_amount, status, created_at, items) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, total_amount, 'pending', datetime.now().isoformat(), str(items))
            )
            await db.commit()
            return cursor.lastrowid

    async def get_orders(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get orders, optionally filtered by user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if user_id:
                cursor = await db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor = await db.execute("SELECT * FROM orders ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_product(self, category_id: int, name: str, description: str, price: float, stock: int) -> None:
        """Add new product"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO products (category_id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
                (category_id, name, description, price, stock)
            )
            await db.commit()

    async def get_stats(self) -> Dict[str, int]:
        """Get admin statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            stats['users'] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM products")
            stats['products'] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM orders")
            stats['orders'] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            stats['pending_orders'] = (await cursor.fetchone())[0]
            
            return stats

    async def get_referral_count(self, user_id: int) -> int:
        """Get number of users referred by this user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
            return (await cursor.fetchone())[0]


# Global database instance
db = Database()
