import aiosqlite
from typing import List, Dict, Optional, Any
from config import settings

DB_PATH = 'cybermarket.db'


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Подключение к базе данных и создание таблиц"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.db:
            await self.db.close()

    async def _create_tables(self) -> None:
        """Создание всех таблиц"""
        await self.db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_code TEXT,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        ''')
        await self.db.commit()

    async def _seed_data(self) -> None:
        """Авто-заполнение демо-данными"""
        # Проверяем, есть ли уже категории
        cursor = await self.db.execute('SELECT COUNT(*) FROM categories')
        count = (await cursor.fetchone())[0]
        if count > 0:
            return

        # Демо-категории
        categories = [
            ('🎮 Игры', 'Цифровые версии популярных игр'),
            ('💻 Софт', 'Лицензионное программное обеспечение'),
            ('🎬 Медиа', 'Фильмы, сериалы и музыка')
        ]

        for name, desc in categories:
            await self.db.execute(
                'INSERT INTO categories (name, description) VALUES (?, ?)',
                (name, desc)
            )

        # Демо-товары
        products = [
            (1, 'Cyberpunk 2077', 'Цифровая версия игры для PC', 1999.0),
            (1, 'Elden Ring', 'Цифровая версия игры для PC', 2499.0),
            (2, 'Windows 11 Pro', 'Лицензионная ОС с ключом активации', 2999.0),
            (3, 'Netflix Premium 1 мес', 'Подписка на месяц', 499.0)
        ]

        for cat_id, name, desc, price in products:
            await self.db.execute(
                'INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)',
                (cat_id, name, desc, price)
            )

        await self.db.commit()

    # ==================== USERS ====================

    async def add_user(self, user_id: int, username: str = None, first_name: str = None,
                       last_name: str = None, referred_by: int = None) -> None:
        """Добавление нового пользователя"""
        referral_code = f'REF{user_id}'
        await self.db.execute('''
            INSERT OR IGNORE INTO users (id, username, first_name, last_name, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, referral_code, referred_by))
        await self.db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        cursor = await self.db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        cursor = await self.db.execute('SELECT * FROM users')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_by_referral(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по реферальному коду"""
        cursor = await self.db.execute('SELECT * FROM users WHERE referral_code = ?', (referral_code,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    # ==================== CATEGORIES ====================

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Получение всех категорий"""
        cursor = await self.db.execute('SELECT * FROM categories')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Получение категории по ID"""
        cursor = await self.db.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_category(self, name: str, description: str = None) -> int:
        """Добавление новой категории"""
        cursor = await self.db.execute(
            'INSERT INTO categories (name, description) VALUES (?, ?)',
            (name, description)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def delete_category(self, category_id: int) -> None:
        """Удаление категории"""
        await self.db.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        await self.db.commit()

    # ==================== PRODUCTS ====================

    async def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Получение товаров по категории"""
        cursor = await self.db.execute(
            'SELECT * FROM products WHERE category_id = ?',
            (category_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получение товара по ID"""
        cursor = await self.db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, name: str, description: str, price: float) -> int:
        """Добавление нового товара"""
        cursor = await self.db.execute(
            'INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)',
            (category_id, name, description, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def delete_product(self, product_id: int) -> None:
        """Удаление товара"""
        await self.db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        await self.db.commit()

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Получение всех товаров"""
        cursor = await self.db.execute('SELECT * FROM products')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ==================== CART ====================

    async def add_to_cart(self, user_id: int, product_id: int, count: int = 1) -> None:
        """Добавление товара в корзину"""
        await self.db.execute('''
            INSERT INTO cart (user_id, product_id, count)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id) 
            DO UPDATE SET count = count + excluded.count
        ''', (user_id, product_id, count))
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение корзины пользователя"""
        cursor = await self.db.execute('''
            SELECT c.*, p.name, p.price, p.description
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Очистка корзины пользователя"""
        await self.db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        await self.db.commit()

    async def remove_from_cart(self, user_id: int, product_id: int) -> None:
        """Удаление товара из корзины"""
        await self.db.execute(
            'DELETE FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        await self.db.commit()

    async def get_cart_total(self, user_id: int) -> float:
        """Получение общей суммы корзины"""
        cursor = await self.db.execute('''
            SELECT SUM(c.count * p.price) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        row = await cursor.fetchone()
        return row['total'] if row and row['total'] else 0.0

    # ==================== ORDERS ====================

    async def create_order(self, user_id: int, total_price: float) -> int:
        """Создание нового заказа"""
        cursor = await self.db.execute(
            'INSERT INTO orders (user_id, total_price) VALUES (?, ?)',
            (user_id, total_price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def add_order_item(self, order_id: int, product_id: int, count: int, price: float) -> None:
        """Добавление товара в заказ"""
        await self.db.execute('''
            INSERT INTO order_items (order_id, product_id, count, price)
            VALUES (?, ?, ?, ?)
        ''', (order_id, product_id, count, price))
        await self.db.commit()

    async def get_orders(self, user_id: int = None) -> List[Dict[str, Any]]:
        """Получение заказов"""
        if user_id:
            cursor = await self.db.execute(
                'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
        else:
            cursor = await self.db.execute('SELECT * FROM orders ORDER BY created_at DESC')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_order_items(self, order_id: int) -> List[Dict[str, Any]]:
        """Получение товаров заказа"""
        cursor = await self.db.execute('''
            SELECT oi.*, p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ==================== STATISTICS ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики для админ-панели"""
        stats = {}

        cursor = await self.db.execute('SELECT COUNT(*) as count FROM users')
        row = await cursor.fetchone()
        stats['users'] = row['count']

        cursor = await self.db.execute('SELECT COUNT(*) as count FROM categories')
        row = await cursor.fetchone()
        stats['categories'] = row['count']

        cursor = await self.db.execute('SELECT COUNT(*) as count FROM products')
        row = await cursor.fetchone()
        stats['products'] = row['count']

        cursor = await self.db.execute('SELECT COUNT(*) as count FROM orders')
        row = await cursor.fetchone()
        stats['orders'] = row['count']

        cursor = await self.db.execute('SELECT COALESCE(SUM(total_price), 0) as total FROM orders')
        row = await cursor.fetchone()
        stats['revenue'] = row['total']

        return stats


# Создаем глобальный экземпляр базы данных
db = Database()
