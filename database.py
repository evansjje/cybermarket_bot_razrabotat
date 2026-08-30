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
        await self.db.execute('PRAGMA foreign_keys = ON')

    async def close(self):
        if self.db:
            await self.db.close()

    async def commit(self):
        if self.db:
            await self.db.commit()

    async def init_db(self):
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        ''')
        await self.commit()

        # Авто-наполнение
        categories_count = await self.db.execute_fetchone('SELECT COUNT(*) FROM categories')
        if categories_count[0] == 0:
            await self.add_category('🎮 Цифровые игры')
            await self.add_category('💎 Подписки')
            await self.add_category('🎁 Подарочные карты')

        products_count = await self.db.execute_fetchone('SELECT COUNT(*) FROM products')
        if products_count[0] == 0:
            categories = await self.get_categories()
            cat_map = {c['title']: c['id'] for c in categories}

            await self.add_product(cat_map['🎮 Цифровые игры'], 'Steam 50$', 'Пополнение кошелька Steam на 50$', 3500)
            await self.add_product(cat_map['🎮 Цифровые игры'], 'Xbox Game Pass Ultimate 1 мес', 'Подписка на 1 месяц', 1200)
            await self.add_product(cat_map['💎 Подписки'], 'Netflix Premium 1 мес', 'Доступ к Netflix Premium на 1 месяц', 800)
            await self.add_product(cat_map['🎁 Подарочные карты'], 'Google Play 1000₽', 'Подарочная карта Google Play на 1000 рублей', 900)

    async def get_categories(self) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        cursor = await self.db.execute('INSERT INTO categories (title) VALUES (?)', (title,))
        await self.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if category_id:
            cursor = await self.db.execute('SELECT * FROM products WHERE category_id = ? ORDER BY id', (category_id,))
        else:
            cursor = await self.db.execute('SELECT * FROM products ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        cursor = await self.db.execute(
            'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
            (category_id, title, desc, price)
        )
        await self.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float):
        await self.db.execute('UPDATE products SET price = ? WHERE id = ?', (price, product_id))
        await self.commit()

    async def update_product_desc(self, product_id: int, desc: str):
        await self.db.execute('UPDATE products SET desc = ? WHERE id = ?', (desc, product_id))
        await self.commit()

    async def delete_product(self, product_id: int):
        await self.db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await self.commit()

    async def add_to_cart(self, user_id: int, product_id: int):
        existing = await self.db.execute_fetchone(
            'SELECT id, count FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        if existing:
            await self.db.execute(
                'UPDATE cart SET count = count + 1 WHERE id = ?',
                (existing['id'],)
            )
        else:
            await self.db.execute(
                'INSERT INTO cart (user_id, product_id) VALUES (?, ?)',
                (user_id, product_id)
            )
        await self.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('''
            SELECT p.id, p.title, p.price, c.count
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.added_at DESC
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int):
        await self.db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await self.commit()

    async def get_stats(self) -> Dict[str, int]:
        users_count = await self.db.execute_fetchone('SELECT COUNT(*) FROM users')
        products_count = await self.db.execute_fetchone('SELECT COUNT(*) FROM products')
        categories_count = await self.db.execute_fetchone('SELECT COUNT(*) FROM categories')
        cart_count = await self.db.execute_fetchone('SELECT COUNT(*) FROM cart')
        return {
            'users': users_count[0],
            'products': products_count[0],
            'categories': categories_count[0],
            'cart_items': cart_count[0]
        }

    async def register_user(self, user_id: int, username: str, first_name: str, last_name: str):
        existing = await self.db.execute_fetchone('SELECT id FROM users WHERE id = ?', (user_id,))
        if not existing:
            await self.db.execute(
                'INSERT INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                (user_id, username, first_name, last_name)
            )
            await self.commit()


db = Database()
