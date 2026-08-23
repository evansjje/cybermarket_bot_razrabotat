import aiosqlite
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class Database:
    """Асинхронный класс для работы с SQLite базой данных."""

    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Устанавливает соединение с базой данных и создает таблицы."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._create_tables()
            logger.info(f"Подключение к базе данных {self.db_path} установлено")

    async def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Соединение с базой данных закрыто")

    @asynccontextmanager
    async def _transaction(self):
        """Контекстный менеджер для транзакций."""
        if not self._connection:
            await self.connect()
        try:
            yield self._connection
            await self._connection.commit()
        except Exception as e:
            await self._connection.rollback()
            logger.error(f"Ошибка транзакции: {e}")
            raise

    async def _create_tables(self) -> None:
        """Создает все необходимые таблицы в базе данных."""
        async with self._transaction() as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0.0,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    total_purchases INTEGER DEFAULT 0,
                    total_spent REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referred_by) REFERENCES users (telegram_id)
                )
            """)

            # Таблица товаров
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица заказов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    payment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)

            # Таблица реферальной системы
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referral_system (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    bonus_amount REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id),
                    UNIQUE(referrer_id, referred_id)
                )
            """)

            # Таблица корзины
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    UNIQUE(user_id, product_id)
                )
            """)

            # Таблица отзывов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)

            # Таблица настроек
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Индексы для оптимизации запросов
            await db.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id)")

            logger.info("Таблицы созданы успешно")

    # ==================== МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ====================

    async def add_user(self, telegram_id: int, username: str = None, 
                       first_name: str = None, last_name: str = None) -> None:
        """Добавляет нового пользователя."""
        async with self._transaction() as db:
            await db.execute(
                """INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
                   VALUES (?, ?, ?, ?)""",
                (telegram_id, username, first_name, last_name)
            )

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о пользователе."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_user(self, telegram_id: int, **kwargs) -> None:
        """Обновляет информацию о пользователе."""
        if not kwargs:
            return
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        async with self._transaction() as db:
            await db.execute(
                f"UPDATE users SET {fields} WHERE telegram_id = ?", values
            )

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей."""
        async with self._transaction() as db:
            cursor = await db.execute("SELECT * FROM users")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== МЕТОДЫ ДЛЯ ТОВАРОВ ====================

    async def add_product(self, name: str, description: str, price: float,
                          category: str, content: str, content_type: str = "text") -> int:
        """Добавляет новый товар."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """INSERT INTO products (name, description, price, category, content, content_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, description, price, category, content, content_type)
            )
            return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получает товар по ID."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Получает товары по категории."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT * FROM products WHERE category = ? AND is_active = 1", (category,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Получает все товары."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT * FROM products WHERE is_active = 1 ORDER BY category, name"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_product(self, product_id: int, **kwargs) -> None:
        """Обновляет информацию о товаре."""
        if not kwargs:
            return
        kwargs['updated_at'] = datetime.now().isoformat()
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        async with self._transaction() as db:
            await db.execute(
                f"UPDATE products SET {fields} WHERE id = ?", values
            )

    async def delete_product(self, product_id: int) -> None:
        """Удаляет товар (мягкое удаление)."""
        async with self._transaction() as db:
            await db.execute(
                "UPDATE products SET is_active = 0 WHERE id = ?", (product_id,)
            )

    async def get_categories(self) -> List[str]:
        """Получает список категорий."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT DISTINCT category FROM products WHERE is_active = 1"
            )
            rows = await cursor.fetchall()
            return [row['category'] for row in rows]

    # ==================== МЕТОДЫ ДЛЯ КОРЗИНЫ ====================

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        """Добавляет товар в корзину."""
        async with self._transaction() as db:
            await db.execute(
                """INSERT OR REPLACE INTO cart (user_id, product_id, quantity)
                   VALUES (?, ?, ?)""",
                (user_id, product_id, quantity)
            )

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает корзину пользователя."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT c.*, p.name, p.price, p.description
                   FROM cart c
                   JOIN products p ON c.product_id = p.id
                   WHERE c.user_id = ? AND p.is_active = 1""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def remove_from_cart(self, user_id: int, product_id: int) -> None:
        """Удаляет товар из корзины."""
        async with self._transaction() as db:
            await db.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )

    async def clear_cart(self, user_id: int) -> None:
        """Очищает корзину пользователя."""
        async with self._transaction() as db:
            await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    async def get_cart_total(self, user_id: int) -> float:
        """Получает общую стоимость корзины."""
        cart = await self.get_cart(user_id)
        return sum(item['price'] * item['quantity'] for item in cart)

    # ==================== МЕТОДЫ ДЛЯ ЗАКАЗОВ ====================

    async def create_order(self, user_id: int, product_id: int, amount: float,
                           payment_method: str = None, payment_id: str = None) -> int:
        """Создает новый заказ."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """INSERT INTO orders (user_id, product_id, amount, payment_method, payment_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, product_id, amount, payment_method, payment_id)
            )
            return cursor.lastrowid

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получает заказ по ID."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT * FROM orders WHERE id = ?", (order_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает все заказы пользователя."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT o.*, p.name as product_name
                   FROM orders o
                   JOIN products p ON o.product_id = p.id
                   WHERE o.user_id = ? ORDER BY o.created_at DESC""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_order_status(self, order_id: int, status: str) -> None:
        """Обновляет статус заказа."""
        async with self._transaction() as db:
            completed_at = datetime.now().isoformat() if status == 'completed' else None
            await db.execute(
                "UPDATE orders SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, order_id)
            )

    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """Получает все заказы."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT o.*, u.username, u.first_name, p.name as product_name
                   FROM orders o
                   JOIN users u ON o.user_id = u.telegram_id
                   JOIN products p ON o.product_id = p.id
                   ORDER BY o.created_at DESC"""
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== МЕТОДЫ ДЛЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ ====================

    async def generate_referral_code(self, telegram_id: int) -> str:
        """Генерирует реферальный код для пользователя."""
        import hashlib
        code = hashlib.md5(f"{telegram_id}{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        async with self._transaction() as db:
            await db.execute(
                "UPDATE users SET referral_code = ? WHERE telegram_id = ?",
                (code, telegram_id)
            )
        return code

    async def get_referral_code(self, telegram_id: int) -> Optional[str]:
        """Получает реферальный код пользователя."""
        user = await self.get_user(telegram_id)
        if user and user.get('referral_code'):
            return user['referral_code']
        return await self.generate_referral_code(telegram_id)

    async def add_referral(self, referrer_id: int, referred_id: int, bonus_amount: float = 0.0) -> None:
        """Добавляет реферальную связь."""
        async with self._transaction() as db:
            await db.execute(
                """INSERT OR IGNORE INTO referral_system (referrer_id, referred_id, bonus_amount)
                   VALUES (?, ?, ?)""",
                (referrer_id, referred_id, bonus_amount)
            )

    async def get_user_referrals(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получает список рефералов пользователя."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT r.*, u.username, u.first_name, u.created_at as user_created_at
                   FROM referral_system r
                   JOIN users u ON r.referred_id = u.telegram_id
                   WHERE r.referrer_id = ?""",
                (telegram_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_referral_stats(self, telegram_id: int) -> Dict[str, Any]:
        """Получает статистику реферальной системы для пользователя."""
        referrals = await self.get_user_referrals(telegram_id)
        total_bonus = sum(r['bonus_amount'] for r in referrals)
        return {
            'total_referrals': len(referrals),
            'total_bonus': total_bonus,
            'referrals': referrals
        }

    # ==================== МЕТОДЫ ДЛЯ ОТЗЫВОВ ====================

    async def add_review(self, user_id: int, product_id: int, rating: int, text: str = None) -> None:
        """Добавляет отзыв."""
        async with self._transaction() as db:
            await db.execute(
                """INSERT INTO reviews (user_id, product_id, rating, text)
                   VALUES (?, ?, ?, ?)""",
                (user_id, product_id, rating, text)
            )

    async def get_product_reviews(self, product_id: int) -> List[Dict[str, Any]]:
        """Получает отзывы о товаре."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT r.*, u.username, u.first_name
                   FROM reviews r
                   JOIN users u ON r.user_id = u.telegram_id
                   WHERE r.product_id = ? ORDER BY r.created_at DESC""",
                (product_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_reviews(self) -> List[Dict[str, Any]]:
        """Получает все отзывы."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT r.*, u.username, u.first_name, p.name as product_name
                   FROM reviews r
                   JOIN users u ON r.user_id = u.telegram_id
                   LEFT JOIN products p ON r.product_id = p.id
                   ORDER BY r.created_at DESC"""
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== МЕТОДЫ ДЛЯ НАСТРОЕК ====================

    async def set_setting(self, key: str, value: str) -> None:
        """Устанавливает настройку."""
        async with self._transaction() as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

    async def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Получает настройку."""
        async with self._transaction() as db:
            cursor = await db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            return row['value'] if row else default

    # ==================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Получает общую статистику магазина."""
        async with self._transaction() as db:
            # Количество пользователей
            cursor = await db.execute("SELECT COUNT(*) as count FROM users")
            users_count = (await cursor.fetchone())['count']

            # Количество товаров
            cursor = await db.execute("SELECT COUNT(*) as count FROM products WHERE is_active = 1")
            products_count = (await cursor.fetchone())['count']

            # Количество заказов
            cursor = await db.execute("SELECT COUNT(*) as count FROM orders")
            orders_count = (await cursor.fetchone())['count']

            # Общая выручка
            cursor = await db.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM orders WHERE status = 'completed'"
            )
            total_revenue = (await cursor.fetchone())['total']

            # Средний чек
            cursor = await db.execute(
                "SELECT COALESCE(AVG(amount), 0) as avg FROM orders WHERE status = 'completed'"
            )
            avg_order = (await cursor.fetchone())['avg']

            return {
                'users_count': users_count,
                'products_count': products_count,
                'orders_count': orders_count,
                'total_revenue': total_revenue,
                'avg_order': avg_order
            }

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Поиск товаров по названию или описанию."""
        async with self._transaction() as db:
            cursor = await db.execute(
                """SELECT * FROM products 
                   WHERE is_active = 1 AND (name LIKE ? OR description LIKE ?)""",
                (f"%{query}%", f"%{query}%")
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# Создаем глобальный экземпляр базы данных
db = Database()

# Функция для получения экземпляра базы данных
async def get_db() -> Database:
    """Возвращает экземпляр базы данных."""
    if db._connection is None:
        await db.connect()
    return db
