# database.py
import aiosqlite
from typing import List, Optional, Dict, Any

DB_PATH = 'cybermarket.db'


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def _connect(self) -> aiosqlite.Connection:
        db = await aiosqlite.connect(self.db_path)
        db.row_factory = aiosqlite.Row
        return db

    async def init_db(self) -> None:
        db = await self._connect()
        await db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT DEFAULT '',
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        await db.commit()
        await self._seed_data(db)
        await db.close()

    async def _seed_data(self, db: aiosqlite.Connection) -> None:
        # Check if categories exist
        cursor = await db.execute('SELECT COUNT(*) FROM categories')
        count = (await cursor.fetchone())[0]
        if count == 0:
            categories = [
                ('Электроника',),
                ('Софт',),
                ('Аккаунты',)
            ]
            await db.executemany('INSERT INTO categories (title) VALUES (?)', categories)
            await db.commit()

            # Get category IDs
            cursor = await db.execute('SELECT id, title FROM categories')
            cat_rows = await cursor.fetchall()
            cat_ids = {row['title']: row['id'] for row in cat_rows}

            products = [
                (cat_ids['Электроника'], 'iPhone 15 Pro', 'Новый iPhone 15 Pro 256GB', 999.99),
                (cat_ids['Электроника'], 'Samsung Galaxy S24', 'Флагман Samsung 2024', 899.99),
                (cat_ids['Софт'], 'Windows 11 Pro', 'Лицензионный ключ Windows 11 Pro', 199.99),
                (cat_ids['Аккаунты'], 'Netflix Premium', 'Аккаунт Netflix Premium на 1 месяц', 9.99),
            ]
            await db.executemany(
                'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
                products
            )
            await db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        db = await self._connect()
        cursor = await db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> None:
        db = await self._connect()
        await db.execute('INSERT INTO categories (title) VALUES (?)', (title,))
        await db.commit()
        await db.close()

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        db = await self._connect()
        if category_id is not None:
            cursor = await db.execute(
                'SELECT * FROM products WHERE category_id = ? ORDER BY id',
                (category_id,)
            )
        else:
            cursor = await db.execute('SELECT * FROM products ORDER BY id')
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        db = await self._connect()
        cursor = await db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = await cursor.fetchone()
        await db.close()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> None:
        db = await self._connect()
        await db.execute(
            'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
            (category_id, title, desc, price)
        )
        await db.commit()
        await db.close()

    async def update_product_price(self, product_id: int, price: float) -> None:
        db = await self._connect()
        await db.execute('UPDATE products SET price = ? WHERE id = ?', (price, product_id))
        await db.commit()
        await db.close()

    async def update_product_desc(self, product_id: int, desc: str) -> None:
        db = await self._connect()
        await db.execute('UPDATE products SET desc = ? WHERE id = ?', (desc, product_id))
        await db.commit()
        await db.close()

    async def delete_product(self, product_id: int) -> None:
        db = await self._connect()
        await db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await db.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
        await db.commit()
        await db.close()

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        db = await self._connect()
        # Check if product already in cart
        cursor = await db.execute(
            'SELECT id, count FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                'UPDATE cart SET count = count + 1 WHERE id = ?',
                (row['id'],)
            )
        else:
            await db.execute(
                'INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, 1)',
                (user_id, product_id)
            )
        await db.commit()
        await db.close()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        db = await self._connect()
        cursor = await db.execute('''
            SELECT p.id, p.title, p.price, c.count
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        db = await self._connect()
        await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await db.commit()
        await db.close()

    async def get_stats(self) -> Dict[str, int]:
        db = await self._connect()
        cursor = await db.execute('SELECT COUNT(*) FROM categories')
        categories = (await cursor.fetchone())[0]
        cursor = await db.execute('SELECT COUNT(*) FROM products')
        products = (await cursor.fetchone())[0]
        cursor = await db.execute('SELECT COUNT(DISTINCT user_id) FROM cart')
        users = (await cursor.fetchone())[0]
        await db.close()
        return {'categories': categories, 'products': products, 'users': users}


db = Database()
