import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Безопасные дефолтные значения для подключения к БД
DB_PATH = Path(__file__).parent / "cybermarket.db"


class Database:
    """Асинхронный класс для работы с SQLite базой данных"""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Установка соединения с базой данных"""
        try:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self.create_tables()
            logger.info(f"Подключение к БД установлено: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    async def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self._connection:
            await self._connection.close()
            logger.info("Соединение с БД закрыто")

    async def create_tables(self) -> None:
        """Создание всех таблиц в базе данных"""
        try:
            # Таблица пользователей
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    balance REAL DEFAULT 0.0,
                    total_purchases INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referred_by) REFERENCES users (telegram_id)
                )
            """)

            # Таблица товаров
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    file_path TEXT,
                    download_link TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица заказов
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    payment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)

            # Таблица реферальной системы
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS referral_system (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    reward_amount REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
                )
            """)

            # Индексы для оптимизации запросов
            await self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id)"
            )
            await self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_products_category ON products (category)"
            )
            await self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id)"
            )
            await self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_referral_referrer ON referral_system (referrer_id)"
            )

            await self._connection.commit()
            logger.info("Таблицы созданы успешно")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    # ==================== МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ====================

    async def add_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        referral_code: str = None,
        referred_by: int = None,
    ) -> bool:
        """Добавление нового пользователя"""
        try:
            # Генерация реферального кода, если не указан
            if not referral_code:
                referral_code = f"REF{telegram_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"

            await self._connection.execute(
                """
                INSERT OR IGNORE INTO users 
                (telegram_id, username, first_name, last_name, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, last_name, referral_code, referred_by),
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по telegram_id"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    async def update_user_balance(self, telegram_id: int, amount: float) -> bool:
        """Обновление баланса пользователя"""
        try:
            await self._connection.execute(
                "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
                (amount, telegram_id),
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления баланса: {e}")
            return False

    async def increment_user_purchases(self, telegram_id: int) -> bool:
        """Увеличение счетчика покупок пользователя"""
        try:
            await self._connection.execute(
                "UPDATE users SET total_purchases = total_purchases + 1 WHERE telegram_id = ?",
                (telegram_id,),
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка увеличения счетчика покупок: {e}")
            return False

    # ==================== МЕТОДЫ ДЛЯ ТОВАРОВ ====================

    async def add_product(
        self,
        name: str,
        description: str,
        price: float,
        category: str,
        file_path: str = None,
        download_link: str = None,
    ) -> int:
        """Добавление нового товара"""
        try:
            cursor = await self._connection.execute(
                """
                INSERT INTO products (name, description, price, category, file_path, download_link)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, description, price, category, file_path, download_link),
            )
            await self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления товара: {e}")
            return 0

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получение товара по ID"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения товара: {e}")
            return None

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Получение всех товаров по категории"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM products WHERE category = ? AND is_active = 1", (category,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения товаров по категории: {e}")
            return []

    async def get_all_categories(self) -> List[str]:
        """Получение всех уникальных категорий"""
        try:
            cursor = await self._connection.execute(
                "SELECT DISTINCT category FROM products WHERE is_active = 1"
            )
            rows = await cursor.fetchall()
            return [row["category"] for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            return []

    async def update_product(
        self,
        product_id: int,
        name: str = None,
        description: str = None,
        price: float = None,
        category: str = None,
        file_path: str = None,
        download_link: str = None,
        is_active: int = None,
    ) -> bool:
        """Обновление информации о товаре"""
        try:
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if price is not None:
                updates.append("price = ?")
                params.append(price)
            if category is not None:
                updates.append("category = ?")
                params.append(category)
            if file_path is not None:
                updates.append("file_path = ?")
                params.append(file_path)
            if download_link is not None:
                updates.append("download_link = ?")
                params.append(download_link)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)

            if not updates:
                return False

            params.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            await self._connection.execute(query, params)
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления товара: {e}")
            return False

    async def delete_product(self, product_id: int) -> bool:
        """Удаление товара"""
        try:
            await self._connection.execute(
                "DELETE FROM products WHERE id = ?", (product_id,)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления товара: {e}")
            return False

    # ==================== МЕТОДЫ ДЛЯ ЗАКАЗОВ ====================

    async def create_order(
        self,
        user_id: int,
        product_id: int,
        amount: float,
        payment_method: str = None,
        payment_id: str = None,
    ) -> int:
        """Создание нового заказа"""
        try:
            cursor = await self._connection.execute(
                """
                INSERT INTO orders (user_id, product_id, amount, payment_method, payment_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, product_id, amount, payment_method, payment_id),
            )
            await self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {e}")
            return 0

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получение заказа по ID"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM orders WHERE id = ?", (order_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения заказа: {e}")
            return None

    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновление статуса заказа"""
        try:
            await self._connection.execute(
                "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заказа: {e}")
            return False

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех заказов пользователя"""
        try:
            cursor = await self._connection.execute(
                """
                SELECT o.*, p.name as product_name, p.file_path, p.download_link
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения заказов пользователя: {e}")
            return []

    # ==================== МЕТОДЫ ДЛЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ ====================

    async def add_referral(
        self,
        referrer_id: int,
        referred_id: int,
        reward_amount: float = 0.0,
    ) -> bool:
        """Добавление реферальной записи"""
        try:
            await self._connection.execute(
                """
                INSERT INTO referral_system (referrer_id, referred_id, reward_amount)
                VALUES (?, ?, ?)
                """,
                (referrer_id, referred_id, reward_amount),
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления реферальной записи: {e}")
            return False

    async def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех рефералов пользователя"""
        try:
            cursor = await self._connection.execute(
                """
                SELECT r.*, u.username, u.first_name, u.last_name
                FROM referral_system r
                JOIN users u ON r.referred_id = u.telegram_id
                WHERE r.referrer_id = ?
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения рефералов: {e}")
            return []

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики реферальной программы"""
        try:
            cursor = await self._connection.execute(
                """
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN status = 'completed' THEN reward_amount ELSE 0 END) as total_reward
                FROM referral_system
                WHERE referrer_id = ?
                """,
                (user_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else {"total_referrals": 0, "total_reward": 0.0}
        except Exception as e:
            logger.error(f"Ошибка получения статистики рефералов: {e}")
            return {"total_referrals": 0, "total_reward": 0.0}

    async def update_referral_status(self, referral_id: int, status: str) -> bool:
        """Обновление статуса реферальной записи"""
        try:
            await self._connection.execute(
                "UPDATE referral_system SET status = ? WHERE id = ?",
                (status, referral_id),
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса реферала: {e}")
            return False

    # ==================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ====================

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Получение всех товаров (для админа)"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM products ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех товаров: {e}")
            return []

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей (для админа)"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей: {e}")
            return []

    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """Получение всех заказов (для админа)"""
        try:
            cursor = await self._connection.execute(
                """
                SELECT o.*, u.username, u.first_name, u.last_name, p.name as product_name
                FROM orders o
                JOIN users u ON o.user_id = u.telegram_id
                JOIN products p ON o.product_id = p.id
                ORDER BY o.created_at DESC
                """
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех заказов: {e}")
            return []

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по реферальному коду"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM users WHERE referral_code = ?", (referral_code,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по реферальному коду: {e}")
            return None

    async def check_user_exists(self, telegram_id: int) -> bool:
        """Проверка существования пользователя"""
        try:
            cursor = await self._connection.execute(
                "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки существования пользователя: {e}")
            return False

    async def get_database_stats(self) -> Dict[str, Any]:
        """Получение общей статистики базы данных"""
        try:
            stats = {}
            
            # Количество пользователей
            cursor = await self._connection.execute("SELECT COUNT(*) as count FROM users")
            row = await cursor.fetchone()
            stats["users"] = row["count"] if row else 0
            
            # Количество товаров
            cursor = await self._connection.execute("SELECT COUNT(*) as count FROM products")
            row = await cursor.fetchone()
            stats["products"] = row["count"] if row else 0
            
            # Количество заказов
            cursor = await self._connection.execute("SELECT COUNT(*) as count FROM orders")
            row = await cursor.fetchone()
            stats["orders"] = row["count"] if row else 0
            
            # Общая выручка
            cursor = await self._connection.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM orders WHERE status = 'completed'"
            )
            row = await cursor.fetchone()
            stats["total_revenue"] = row["total"] if row else 0.0
            
            return stats
        except Exception as e:
            logger.error(f"Ошибка получения статистики БД: {e}")
            return {"users": 0, "products": 0, "orders": 0, "total_revenue": 0.0}


# Создание глобального экземпляра базы данных
db = Database()
