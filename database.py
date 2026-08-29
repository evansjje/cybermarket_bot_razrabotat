# database.py
import aiosqlite
from typing import List, Dict, Optional, Any


class Database:
    def __init__(self, db_path: str = 'cybermarket.db'):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Подключение к базе данных и создание таблиц"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def _create_tables(self) -> None:
        """Создание таблиц"""
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
                price REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.commit()

    async def _seed_data(self) -> None:
        """Авто-наполнение 3 категорий и 4 товаров"""
        # Проверяем, есть ли уже данные
        cursor = await self.db.execute('SELECT COUNT(*) FROM categories')
        count = (await cursor.fetchone())[0]
        if count > 0:
            return

        # Категории
        categories = ['💻 Программы', '🎮 Игры', '🎵 Медиа']
        for cat in categories:
            await self.db.execute(
                'INSERT INTO categories (title) VALUES (?)',
                (cat,)
            )

        # Товары
        products = [
            (1, 'Windows 11 Pro', 'Лицензионный ключ активации', 1999),
            (1, 'Microsoft Office 2021', 'Полный пакет офисных программ', 2499),
            (2, 'Cyberpunk 2077', 'Цифровая версия игры', 1499),
            (3, 'Музыкальный пакет', '1000+ треков в MP3', 499)
        ]
        for prod in products:
            await self.db.execute(
                'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
                prod
            )
        await self.db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Получение всех категорий"""
        cursor = await self.db.execute('SELECT * FROM categories ORDER BY id')
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        """Добавление новой категории"""
        cursor = await self.db.execute(
            'INSERT INTO categories (title) VALUES (?)',
            (title,)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение товаров (всех или по категории)"""
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
        """Получение товара по ID"""
        cursor = await self.db.execute(
            'SELECT * FROM products WHERE id = ?',
            (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        """Добавление нового товара"""
        cursor = await self.db.execute(
            'INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)',
            (category_id, title, desc, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float) -> None:
        """Обновление цены товара"""
        await self.db.execute(
            'UPDATE products SET price = ? WHERE id = ?',
            (price, product_id)
        )
        await self.db.commit()

    async def update_product_desc(self, product_id: int, desc: str) -> None:
        """Обновление описания товара"""
        await self.db.execute(
            'UPDATE products SET desc = ? WHERE id = ?',
            (desc, product_id)
        )
        await self.db.commit()

    async def delete_product(self, product_id: int) -> None:
        """Удаление товара"""
        # Удаляем товар из корзины
        await self.db.execute(
            'DELETE FROM cart WHERE product_id = ?',
            (product_id,)
        )
        # Удаляем сам товар
        await self.db.execute(
            'DELETE FROM products WHERE id = ?',
            (product_id,)
        )
        await self.db.commit()

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        """Добавление товара в корзину"""
        # Проверяем, есть ли уже такой товар в корзине
        cursor = await self.db.execute(
            'SELECT * FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            # Увеличиваем количество
            await self.db.execute(
                'UPDATE cart SET count = count + 1 WHERE user_id = ? AND product_id = ?',
                (user_id, product_id)
            )
        else:
            # Добавляем новый товар
            await self.db.execute(
                'INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, 1)',
                (user_id, product_id)
            )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение корзины пользователя"""
        cursor = await self.db.execute('''
            SELECT 
                c.id as cart_id,
                c.product_id,
                c.count,
                p.title,
                p.price,
                p.desc
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.id
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Очистка корзины пользователя"""
        await self.db.execute(
            'DELETE FROM cart WHERE user_id = ?',
            (user_id,)
        )
        await self.db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики магазина"""
        # Количество пользователей
        cursor = await self.db.execute('SELECT COUNT(DISTINCT user_id) FROM users')
        users_count = (await cursor.fetchone())[0]
        
        # Количество товаров
        cursor = await self.db.execute('SELECT COUNT(*) FROM products')
        products_count = (await cursor.fetchone())[0]
        
        # Количество категорий
        cursor = await self.db.execute('SELECT COUNT(*) FROM categories')
        categories_count = (await cursor.fetchone())[0]
        
        # Общая выручка (сумма всех товаров в корзинах)
        cursor = await self.db.execute('''
            SELECT SUM(p.price * c.count) as total
            FROM cart c
            JOIN products p ON c.product_id = p.id
        ''')
        row = await cursor.fetchone()
        total_revenue = row['total'] if row and row['total'] else 0
        
        return {
            'users_count': users_count,
            'products_count': products_count,
            'categories_count': categories_count,
            'total_revenue': total_revenue
        }

    async def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> None:
        """Регистрация пользователя"""
        await self.db.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        await self.db.commit()

    async def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.db:
            await self.db.close()


# Создаем глобальный экземпляр базы данных
db = Database()
