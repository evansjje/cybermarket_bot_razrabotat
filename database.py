import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'cybermarket.db')


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                title TEXT NOT NULL,
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
                total REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        await db.commit()

        # Auto-seed demo data
        cursor = await db.execute('SELECT COUNT(*) FROM categories')
        count = (await cursor.fetchone())[0]
        if count == 0:
            demo_categories = [
                ('🎮 Игры',),
                ('💻 Софт',),
                ('🎁 Подарки',)
            ]
            await db.executemany('INSERT INTO categories (name) VALUES (?)', demo_categories)
            await db.commit()

            cursor = await db.execute('SELECT id FROM categories')
            cat_ids = [row[0] for row in await cursor.fetchall()]

            demo_products = [
                (cat_ids[0], 'Steam Gift Card 10$', 'Цифровой код пополнения Steam на 10$', 850.0),
                (cat_ids[0], 'Xbox Game Pass Ultimate 1 месяц', 'Подписка Xbox Game Pass Ultimate на 1 месяц', 499.0),
                (cat_ids[1], 'Windows 11 Pro Key', 'Лицензионный ключ активации Windows 11 Pro', 1990.0),
                (cat_ids[2], 'Telegram Premium 1 месяц', 'Подарочная подписка Telegram Premium на 1 месяц', 299.0),
            ]
            await db.executemany(
                'INSERT INTO products (category_id, title, description, price) VALUES (?, ?, ?, ?)',
                demo_products
            )
            await db.commit()


async def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            'INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
            (user_id, username, first_name, last_name)
        )
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_products_by_category(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM products WHERE category_id = ? ORDER BY id', (category_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_product(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_to_cart(user_id: int, product_id: int, count: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
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


async def get_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT c.product_id, c.count, p.title, p.price, p.description
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.product_id
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def clear_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await db.commit()


async def get_cart_total(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT SUM(p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        row = await cursor.fetchone()
        return row['total'] if row and row['total'] else 0.0


async def create_order(user_id: int, total: float):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'INSERT INTO orders (user_id, total) VALUES (?, ?)',
            (user_id, total)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        ''')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
        await db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT COUNT(*) as users FROM users')
        users = (await cursor.fetchone())['users']
        cursor = await db.execute('SELECT COUNT(*) as products FROM products')
        products = (await cursor.fetchone())['products']
        cursor = await db.execute('SELECT COUNT(*) as orders FROM orders')
        orders = (await cursor.fetchone())['orders']
        return {'users': users, 'products': products, 'orders': orders}
