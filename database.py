# database.py
import aiosqlite
from typing import List, Optional, Tuple, Any

DB_PATH = 'cybermarket.db'


async def init_db() -> None:
    """Initialize database and create tables if not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create tables
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_code TEXT,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        await db.commit()
        
        # Auto-populate demo data
        await seed_demo_data(db)


async def seed_demo_data(db: aiosqlite.Connection) -> None:
    """Insert demo categories and products if database is empty."""
    # Check if categories exist
    cursor = await db.execute('SELECT COUNT(*) FROM categories')
    count = (await cursor.fetchone())[0]
    
    if count == 0:
        # Insert demo categories
        categories = [
            ('🎮 Игры',),
            ('💻 Софт',),
            ('🎁 Подарки',)
        ]
        await db.executemany('INSERT INTO categories (name) VALUES (?)', categories)
        
        # Get category IDs
        cursor = await db.execute('SELECT id, name FROM categories')
        cat_map = {name: id for id, name in await cursor.fetchall()}
        
        # Insert demo products
        products = [
            (cat_map['🎮 Игры'], 'Steam Gift Card 100₽', 'Пополнение кошелька Steam на 100 рублей', 120.0),
            (cat_map['🎮 Игры'], 'Xbox Game Pass 1 месяц', 'Подписка Xbox Game Pass на 1 месяц', 499.0),
            (cat_map['💻 Софт'], 'Windows 10 Pro Key', 'Лицензионный ключ Windows 10 Pro', 199.0),
            (cat_map['💻 Софт'], 'Office 365 1 год', 'Подписка Office 365 на 1 год', 999.0),
        ]
        await db.executemany(
            'INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)',
            products
        )
        
        await db.commit()


async def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None) -> None:
    """Add new user to database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (id, username, first_name, last_name, referred_by) VALUES (?, ?, ?, ?, ?)',
            (user_id, username, first_name, last_name, referred_by)
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[Tuple]:
    """Get user by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return await cursor.fetchone()


async def get_all_categories() -> List[Tuple]:
    """Get all categories."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, name FROM categories ORDER BY id')
        return await cursor.fetchall()


async def get_categories() -> List[Tuple]:
    """Get all categories (alias for get_all_categories)."""
    return await get_all_categories()


async def get_products_by_category(category_id: int) -> List[Tuple]:
    """Get products by category ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT id, name, description, price FROM products WHERE category_id = ? ORDER BY id',
            (category_id,)
        )
        return await cursor.fetchall()


async def get_product(product_id: int) -> Optional[Tuple]:
    """Get product by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT id, category_id, name, description, price FROM products WHERE id = ?',
            (product_id,)
        )
        return await cursor.fetchone()


async def add_to_cart(user_id: int, product_id: int, count: int = 1) -> None:
    """Add product to user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if product already in cart
        cursor = await db.execute(
            'SELECT count FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            await db.execute(
                'UPDATE cart SET count = count + ? WHERE user_id = ? AND product_id = ?',
                (count, user_id, product_id)
            )
        else:
            await db.execute(
                'INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, ?)',
                (user_id, product_id, count)
            )
        await db.commit()


async def get_cart(user_id: int) -> List[Tuple]:
    """Get user's cart with product details."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT c.product_id, p.name, p.price, c.count, (p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.product_id
        ''', (user_id,))
        return await cursor.fetchall()


async def get_cart_total(user_id: int) -> float:
    """Get total price of user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT SUM(p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result and result[0] else 0.0


async def clear_cart(user_id: int) -> None:
    """Clear user's cart."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await db.commit()


async def create_order(user_id: int, product_id: int, count: int, total_price: float) -> int:
    """Create new order and return order ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'INSERT INTO orders (user_id, product_id, count, total_price) VALUES (?, ?, ?, ?)',
            (user_id, product_id, count, total_price)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_products() -> List[Tuple]:
    """Get all products with category names."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT p.id, p.name, p.description, p.price, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        ''')
        return await cursor.fetchall()


async def get_stats() -> Tuple[int, int, int]:
    """Get statistics: users count, products count, orders count."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM users')
        users = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM products')
        products = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM orders')
        orders = (await cursor.fetchone())[0]
        
        return users, products, orders


async def add_product(category_id: int, name: str, description: str, price: float) -> None:
    """Add new product to database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)',
            (category_id, name, description, price)
        )
        await db.commit()


async def get_category_by_name(name: str) -> Optional[Tuple]:
    """Get category by name."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT id, name FROM categories WHERE name = ?', (name,))
        return await cursor.fetchone()


async def add_category(name: str) -> int:
    """Add new category and return its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        await db.commit()
        return cursor.lastrowid


class Database:
    """Database wrapper class for synchronous access patterns."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    async def get_categories(self) -> List[Tuple]:
        """Get all categories."""
        return await get_categories()
    
    async def get_all_categories(self) -> List[Tuple]:
        """Get all categories."""
        return await get_all_categories()
    
    async def get_products_by_category(self, category_id: int) -> List[Tuple]:
        """Get products by category ID."""
        return await get_products_by_category(category_id)
    
    async def get_product(self, product_id: int) -> Optional[Tuple]:
        """Get product by ID."""
        return await get_product(product_id)
    
    async def add_to_cart(self, user_id: int, product_id: int, count: int = 1) -> None:
        """Add product to user's cart."""
        await add_to_cart(user_id, product_id, count)
    
    async def get_cart(self, user_id: int) -> List[Tuple]:
        """Get user's cart with product details."""
        return await get_cart(user_id)
    
    async def get_cart_total(self, user_id: int) -> float:
        """Get total price of user's cart."""
        return await get_cart_total(user_id)
    
    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart."""
        await clear_cart(user_id)
    
    async def create_order(self, user_id: int, product_id: int, count: int, total_price: float) -> int:
        """Create new order and return order ID."""
        return await create_order(user_id, product_id, count, total_price)
    
    async def get_all_products(self) -> List[Tuple]:
        """Get all products with category names."""
        return await get_all_products()
    
    async def get_stats(self) -> Tuple[int, int, int]:
        """Get statistics: users count, products count, orders count."""
        return await get_stats()
    
    async def add_product(self, category_id: int, name: str, description: str, price: float) -> None:
        """Add new product to database."""
        await add_product(category_id, name, description, price)
    
    async def get_category_by_name(self, name: str) -> Optional[Tuple]:
        """Get category by name."""
        return await get_category_by_name(name)
    
    async def add_category(self, name: str) -> int:
        """Add new category and return its ID."""
        return await add_category(name)
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None) -> None:
        """Add new user to database."""
        await add_user(user_id, username, first_name, last_name, referred_by)
    
    async def get_user(self, user_id: int) -> Optional[Tuple]:
        """Get user by ID."""
        return await get_user(user_id)
