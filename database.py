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
        await self._create_tables()
        await self._seed_data()

    async def close(self):
        if self.db:
            await self.db.close()

    async def _create_tables(self):
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
                desc TEXT DEFAULT '',
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.commit()

    async def _seed_data(self):
        # Check if categories exist
        cursor = await self.db.execute('SELECT COUNT(*) FROM categories')
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = [
                ('🎮 Игры',),
                ('💻 ПО',),
                ('🎁 Подарки',)
            ]
            await self.db.executemany('INSERT INTO categories (title) VALUES (?)', categories)
            await self.db.commit()

            # Get category IDs
            cursor = await self.db.execute('SELECT id, title FROM categories')
            cat_rows = await cursor.fetchall()
            cat_map = {row['title']: row['id'] for row in cat_rows}

            products = [
                (cat_map['🎮 Игры'], 'Steam Gift Card 50$', 'Цифровая подарочная карта Steam на 50$', 49.99),
                (cat_map['🎮 Игры'], 'Xbox Game Pass Ultimate 1 мес', 'Подписка Xbox Game Pass Ultimate на 1 месяц', 14.99),
                (cat_map['💻 ПО'], 'Windows 11 Pro Key', 'Лицензионный ключ Windows 11 Pro', 25.00),
                (cat_map['💻 ПО'], 'Office 2021 Pro Plus', 'Лицензионный ключ Microsoft Office 2021', 35.00),
            ]
            await self.db.executemany(
                'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
                products
            )
            await self.db.commit()

    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        await self.db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
            (user_id, username, first_name)
        )
        await self.db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        cursor = await self.db.execute('INSERT INTO categories (title) VALUES (?)', (title,))
        await self.db.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if category_id is not None:
            cursor = await self.db.execute(
                'SELECT * FROM products WHERE category_id = ? ORDER BY id',
                (category_id,)
            )
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
        await self.db.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float):
        await self.db.execute(
            'UPDATE products SET price = ? WHERE id = ?',
            (price, product_id)
        )
        await self.db.commit()

    async def update_product_desc(self, product_id: int, desc: str):
        await self.db.execute(
            'UPDATE products SET desc = ? WHERE id = ?',
            (desc, product_id)
        )
        await self.db.commit()

    async def delete_product(self, product_id: int):
        await self.db.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
        await self.db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await self.db.commit()

    async def add_to_cart(self, user_id: int, product_id: int):
        await self.db.execute('''
            INSERT INTO cart (user_id, product_id, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, product_id) DO UPDATE SET count = count + 1
        ''', (user_id, product_id))
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('''
            SELECT p.id, p.title, p.desc, p.price, c.count
            FROM cart c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ?
            ORDER BY c.id
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int):
        await self.db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict[str, int]:
        cursor = await self.db.execute('SELECT COUNT(*) FROM users')
        users = (await cursor.fetchone())[0]

        cursor = await self.db.execute('SELECT COUNT(*) FROM products')
        products = (await cursor.fetchone())[0]

        cursor = await self.db.execute('SELECT COUNT(*) FROM categories')
        categories = (await cursor.fetchone())[0]

        cursor = await self.db.execute('SELECT COUNT(*) FROM cart')
        cart_items = (await cursor.fetchone())[0]

        return {
            'users': users,
            'products': products,
            'categories': categories,
            'cart_items': cart_items
        }


db = Database()
