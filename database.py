import aiosqlite
from typing import List, Dict, Optional, Any

DB_PATH = 'cybermarket.db'


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def close(self) -> None:
        if self.db:
            await self.db.close()

    async def _create_tables(self) -> None:
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        await self.db.commit()

    async def _seed_data(self) -> None:
        # Check if categories exist
        cursor = await self.db.execute('SELECT COUNT(*) FROM categories')
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = [
                ('🎮 Игры',),
                ('💻 Софт',),
                ('🎁 Подарки',)
            ]
            await self.db.executemany('INSERT INTO categories (name) VALUES (?)', categories)
            await self.db.commit()

            # Get category IDs
            cursor = await self.db.execute('SELECT id, name FROM categories')
            cat_rows = await cursor.fetchall()
            cat_ids = {row['name']: row['id'] for row in cat_rows}

            products = [
                (cat_ids['🎮 Игры'], 'Steam Gift Card 50$', 'Пополнение кошелька Steam на 50$', 49.99),
                (cat_ids['🎮 Игры'], 'Xbox Game Pass Ultimate 1 мес', 'Подписка на 1 месяц', 14.99),
                (cat_ids['💻 Софт'], 'Windows 11 Pro Key', 'Лицензионный ключ активации', 19.99),
                (cat_ids['💻 Софт'], 'Office 2021 Pro Plus', 'Лицензионный ключ активации', 24.99),
            ]
            await self.db.executemany(
                'INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)',
                products
            )
            await self.db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if category_id:
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

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
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
                'INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, 1)',
                (user_id, product_id)
            )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = await self.db.execute('''
            SELECT c.product_id, c.count, p.name, p.price, p.description
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.product_id
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        await self.db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await self.db.commit()

    async def delete_product(self, product_id: int) -> None:
        await self.db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await self.db.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict[str, int]:
        cursor = await self.db.execute('SELECT COUNT(*) as cnt FROM users')
        users = (await cursor.fetchone())['cnt']

        cursor = await self.db.execute('SELECT COUNT(*) as cnt FROM orders')
        orders = (await cursor.fetchone())['cnt']

        cursor = await self.db.execute('SELECT COALESCE(SUM(total_amount), 0) as total FROM orders')
        revenue = (await cursor.fetchone())['total']

        return {'users': users, 'orders': orders, 'revenue': revenue}

    async def get_referrals_count(self, user_id: Optional[int] = None) -> int:
        if user_id is None:
            return 0
        cursor = await self.db.execute(
            'SELECT COUNT(*) as cnt FROM users WHERE referral_id = ?',
            (user_id,)
        )
        row = await cursor.fetchone()
        return row['cnt'] if row else 0

    async def add_user(self, user_id: int, username: str = None, first_name: str = None,
                       last_name: str = None, referral_id: Optional[int] = None) -> None:
        cursor = await self.db.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        existing = await cursor.fetchone()
        if not existing:
            await self.db.execute(
                'INSERT INTO users (id, username, first_name, last_name, referral_id) VALUES (?, ?, ?, ?, ?)',
                (user_id, username, first_name, last_name, referral_id)
            )
            await self.db.commit()

    async def create_order(self, user_id: int, total_amount: float) -> int:
        cursor = await self.db.execute(
            'INSERT INTO orders (user_id, total_amount) VALUES (?, ?)',
            (user_id, total_amount)
        )
        await self.db.commit()
        return cursor.lastrowid


db = Database()
