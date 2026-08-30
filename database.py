# database.py
import aiosqlite
from typing import List, Optional, Dict, Any

DB_PATH = 'cybermarket.db'


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.init_db()

    async def close(self):
        if self.db:
            await self.db.close()

    async def init_db(self):
        """Initialize database tables and seed data if empty."""
        async with self.db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT DEFAULT '',
                price REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        '''):
            pass

        await self.db.commit()

        # Auto-seed data if empty
        categories_count = await self.get_categories_count()
        if categories_count == 0:
            await self.seed_categories()

        products_count = await self.get_products_count()
        if products_count == 0:
            await self.seed_products()

    async def get_categories_count(self) -> int:
        cursor = await self.db.execute('SELECT COUNT(*) as count FROM categories')
        row = await cursor.fetchone()
        return row['count'] if row else 0

    async def get_products_count(self) -> int:
        cursor = await self.db.execute('SELECT COUNT(*) as count FROM products')
        row = await cursor.fetchone()
        return row['count'] if row else 0

    async def seed_categories(self):
        categories = ['🎮 Игры', '💻 Софт', '🎁 Подарки']
        for cat in categories:
            await self.add_category(cat)

    async def seed_products(self):
        products = [
            (1, 'Steam Gift Card 100₽', 'Пополнение Steam на 100 рублей', 100.0),
            (1, 'Steam Gift Card 500₽', 'Пополнение Steam на 500 рублей', 500.0),
            (2, 'Windows 10 Pro Key', 'Лицензионный ключ Windows 10 Pro', 1500.0),
            (3, 'Discord Nitro 1 месяц', 'Подписка Discord Nitro на 1 месяц', 299.0),
        ]
        for cat_id, title, desc, price in products:
            await self.add_product(cat_id, title, desc, price)

    async def get_categories(self) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def add_category(self, title: str) -> int:
        cursor = await self.db.execute('INSERT INTO categories (title) VALUES (?)', (title,))
        await self.db.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if category_id:
            cursor = await self.db.execute(
                'SELECT * FROM products WHERE category_id = ? ORDER BY id', (category_id,)
            )
        else:
            cursor = await self.db.execute('SELECT * FROM products ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        cursor = await self.db.execute(
            'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
            (category_id, title, desc, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float):
        await self.db.execute('UPDATE products SET price = ? WHERE id = ?', (price, product_id))
        await self.db.commit()

    async def update_product_desc(self, product_id: int, desc: str):
        await self.db.execute('UPDATE products SET desc = ? WHERE id = ?', (desc, product_id))
        await self.db.commit()

    async def delete_product(self, product_id: int):
        await self.db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await self.db.commit()

    async def add_to_cart(self, user_id: int, product_id: int):
        # Check if product already in cart
        cursor = await self.db.execute(
            'SELECT * FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        if existing:
            await self.db.execute(
                'UPDATE cart SET count = count + 1 WHERE user_id = ? AND product_id = ?',
                (user_id, product_id)
            )
        else:
            await self.db.execute(
                'INSERT INTO cart (user_id, product_id) VALUES (?, ?)',
                (user_id, product_id)
            )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('''
            SELECT c.id, c.product_id, c.count, p.title, p.price, p.desc
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.id
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def clear_cart(self, user_id: int):
        await self.db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        stats = {}
        
        # Users count
        cursor = await self.db.execute('SELECT COUNT(*) as count FROM users')
        row = await cursor.fetchone()
        stats['users'] = row['count'] if row else 0
        
        # Categories count
        cursor = await self.db.execute('SELECT COUNT(*) as count FROM categories')
        row = await cursor.fetchone()
        stats['categories'] = row['count'] if row else 0
        
        # Products count
        cursor = await self.db.execute('SELECT COUNT(*) as count FROM products')
        row = await cursor.fetchone()
        stats['products'] = row['count'] if row else 0
        
        # Cart items count
        cursor = await self.db.execute('SELECT COUNT(*) as count FROM cart')
        row = await cursor.fetchone()
        stats['cart_items'] = row['count'] if row else 0
        
        # Total revenue (sum of all products in cart)
        cursor = await self.db.execute('''
            SELECT SUM(p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
        ''')
        row = await cursor.fetchone()
        stats['total_revenue'] = row['total'] if row and row['total'] else 0
        
        return stats

    async def register_user(self, user_id: int, username: str, first_name: str, last_name: str):
        cursor = await self.db.execute(
            'SELECT id FROM users WHERE id = ?', (user_id,)
        )
        existing = await cursor.fetchone()
        if not existing:
            await self.db.execute(
                'INSERT INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                (user_id, username, first_name, last_name)
            )
            await self.db.commit()


# Global database instance
db = Database()
