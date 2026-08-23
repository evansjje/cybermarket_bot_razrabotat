import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'cybermarket.db')


async def init_db():
    """Инициализация базы данных и создание таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Создание таблиц
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
                desc TEXT,
                price REAL NOT NULL,
                file_data TEXT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        await db.commit()
        
        # Заполнение демо-данными
        await seed_demo_data(db)


async def seed_demo_data(db):
    """Заполнение базы демо-данными"""
    # Проверяем, есть ли уже категории
    cursor = await db.execute('SELECT COUNT(*) FROM categories')
    count = (await cursor.fetchone())[0]
    
    if count == 0:
        # Добавляем категории
        categories = ['Скрипты', 'Курсы', 'Софт']
        for cat in categories:
            await db.execute('INSERT INTO categories (name) VALUES (?)', (cat,))
        
        # Получаем ID категорий
        cursor = await db.execute('SELECT id, name FROM categories')
        cat_ids = {name: id for id, name in await cursor.fetchall()}
        
        # Добавляем товары
        products = [
            (cat_ids['Скрипты'], 'Python-скрипт для парсинга', 'Готовый скрипт для парсинга сайтов с использованием BeautifulSoup и requests. Включает документацию.', 499.0, 'script_data_1'),
            (cat_ids['Скрипты'], 'Telegram-бот для рассылки', 'Универсальный бот для массовой рассылки сообщений. Поддержка HTML-разметки, кнопок и медиа.', 799.0, 'script_data_2'),
            (cat_ids['Курсы'], 'Курс по Python для начинающих', 'Полный курс по Python с нуля: основы, ООП, работа с базами данных, создание ботов. 50+ уроков.', 1999.0, 'course_data_1'),
            (cat_ids['Софт'], 'Антивирус Pro 2024', 'Современный антивирус с защитой от всех типов угроз. Лицензия на 1 год.', 1499.0, 'soft_data_1')
        ]
        
        for product in products:
            await db.execute(
                'INSERT INTO products (category_id, title, desc, price, file_data) VALUES (?, ?, ?, ?, ?)',
                product
            )
        
        await db.commit()


async def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Добавление нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
            (user_id, username, first_name, last_name)
        )
        await db.commit()


async def get_user(user_id: int):
    """Получение пользователя по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return await cursor.fetchone()


async def get_categories():
    """Получение всех категорий"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM categories')
        return await cursor.fetchall()


async def get_products_by_category(category_id: int):
    """Получение товаров по категории"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM products WHERE category_id = ?', (category_id,))
        return await cursor.fetchall()


async def get_product(product_id: int):
    """Получение товара по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        return await cursor.fetchone()


async def add_to_cart(user_id: int, product_id: int, count: int = 1):
    """Добавление товара в корзину"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже такой товар в корзине
        cursor = await db.execute(
            'SELECT count FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            new_count = existing[0] + count
            await db.execute(
                'UPDATE cart SET count = ? WHERE user_id = ? AND product_id = ?',
                (new_count, user_id, product_id)
            )
        else:
            await db.execute(
                'INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, ?)',
                (user_id, product_id, count)
            )
        await db.commit()


async def get_cart(user_id: int):
    """Получение корзины пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT c.product_id, p.title, p.price, c.count, p.desc
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        return await cursor.fetchall()


async def update_cart_count(user_id: int, product_id: int, count: int):
    """Обновление количества товара в корзине"""
    async with aiosqlite.connect(DB_PATH) as db:
        if count <= 0:
            await db.execute(
                'DELETE FROM cart WHERE user_id = ? AND product_id = ?',
                (user_id, product_id)
            )
        else:
            await db.execute(
                'UPDATE cart SET count = ? WHERE user_id = ? AND product_id = ?',
                (count, user_id, product_id)
            )
        await db.commit()


async def clear_cart(user_id: int):
    """Очистка корзины пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await db.commit()


async def create_order(user_id: int, product_id: int, count: int, total_price: float):
    """Создание заказа"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO orders (user_id, product_id, count, total_price) VALUES (?, ?, ?, ?)',
            (user_id, product_id, count, total_price)
        )
        await db.commit()


async def get_user_stats():
    """Получение статистики пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM users')
        users_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM orders')
        orders_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM products')
        products_count = (await cursor.fetchone())[0]
        
        return {
            'users': users_count,
            'orders': orders_count,
            'products': products_count
        }


async def add_product(category_id: int, title: str, desc: str, price: float, file_data: str = None):
    """Добавление нового товара"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO products (category_id, title, desc, price, file_data) VALUES (?, ?, ?, ?, ?)',
            (category_id, title, desc, price, file_data)
        )
        await db.commit()


async def get_all_products():
    """Получение всех товаров"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM products')
        return await cursor.fetchall()
