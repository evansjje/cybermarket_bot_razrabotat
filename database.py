import aiosqlite
from typing import List, Dict, Optional, Any
import os

DB_PATH = "cybermarket.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Устанавливает соединение с базой данных и создает таблицы."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.db:
            await self.db.close()

    async def _create_tables(self) -> None:
        """Создает таблицы, если они не существуют."""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_code TEXT,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await self.db.execute("""
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
        """)
        await self.db.commit()

    async def _seed_data(self) -> None:
        """Заполняет базу данных демо-данными при первом запуске."""
        # Проверяем, есть ли уже категории
        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return

        # Демо-категории
        categories = [
            ("🎮 Игры",),
            ("💻 Программы",),
            ("🎵 Медиа",)
        ]
        await self.db.executemany(
            "INSERT INTO categories (name) VALUES (?)", categories
        )

        # Демо-товары
        products = [
            (1, "Cyberpunk 2077", "Полная версия игры для PC", 2999.0),
            (1, "GTA V", "Лицензионная версия игры", 1999.0),
            (2, "Windows 11 Pro", "Официальная лицензия", 4999.0),
            (3, "Музыкальный пакет", "1000 треков в MP3", 499.0)
        ]
        await self.db.executemany(
            """INSERT INTO products (category_id, name, description, price)
               VALUES (?, ?, ?, ?)""", products
        )
        await self.db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Возвращает список всех категорий."""
        cursor = await self.db.execute("SELECT * FROM categories")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Возвращает список товаров, опционально по категории."""
        if category_id:
            cursor = await self.db.execute(
                "SELECT * FROM products WHERE category_id = ?", (category_id,)
            )
        else:
            cursor = await self.db.execute("SELECT * FROM products")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает товар по его ID."""
        cursor = await self.db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        """Добавляет товар в корзину пользователя."""
        await self.db.execute("""
            INSERT INTO cart (user_id, product_id, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, product_id) 
            DO UPDATE SET count = count + 1
        """, (user_id, product_id))
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Возвращает корзину пользователя с деталями товаров."""
        cursor = await self.db.execute("""
            SELECT c.product_id, c.count, p.name, p.price, p.description
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Очищает корзину пользователя."""
        await self.db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def delete_product(self, product_id: int) -> None:
        """Удаляет товар из базы данных."""
        await self.db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику бота."""
        stats = {}
        
        # Количество пользователей
        cursor = await self.db.execute("SELECT COUNT(*) FROM users")
        stats['users'] = (await cursor.fetchone())[0]
        
        # Количество товаров
        cursor = await self.db.execute("SELECT COUNT(*) FROM products")
        stats['products'] = (await cursor.fetchone())[0]
        
        # Количество категорий
        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        stats['categories'] = (await cursor.fetchone())[0]
        
        # Количество заказов
        cursor = await self.db.execute("SELECT COUNT(*) FROM orders")
        stats['orders'] = (await cursor.fetchone())[0]
        
        return stats

    async def get_referrals_count(self, user_id: int) -> int:
        """Возвращает количество рефералов пользователя."""
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)
        )
        return (await cursor.fetchone())[0]

    async def add_user(self, user_id: int, username: str, first_name: str, 
                       last_name: str, referral_code: str = None, 
                       referred_by: int = None) -> None:
        """Добавляет нового пользователя в базу данных."""
        await self.db.execute("""
            INSERT OR IGNORE INTO users 
            (id, username, first_name, last_name, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, referral_code, referred_by))
        await self.db.commit()

    async def add_category(self, name: str) -> None:
        """Добавляет новую категорию."""
        await self.db.execute(
            "INSERT INTO categories (name) VALUES (?)", (name,)
        )
        await self.db.commit()

    async def add_product(self, category_id: int, name: str, 
                          description: str, price: float) -> None:
        """Добавляет новый товар."""
        await self.db.execute("""
            INSERT INTO products (category_id, name, description, price)
            VALUES (?, ?, ?, ?)
        """, (category_id, name, description, price))
        await self.db.commit()

    async def create_order(self, user_id: int, product_id: int, 
                           count: int, total_price: float) -> None:
        """Создает заказ."""
        await self.db.execute("""
            INSERT INTO orders (user_id, product_id, count, total_price)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, count, total_price))
        await self.db.commit()


# Создаем глобальный экземпляр базы данных
db = Database()
