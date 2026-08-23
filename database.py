import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import settings

class Database:
    """Асинхронный класс для работы с SQLite базой данных."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Устанавливает соединение с базой данных."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._create_tables()

    async def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _create_tables(self) -> None:
        """Создает все необходимые таблицы, если они не существуют."""
        await self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                file_path TEXT,
                content TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                total_price REAL NOT NULL,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS referral_system (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_user_id INTEGER NOT NULL,
                reward_amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id),
                FOREIGN KEY (referred_user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        """)
        await self._connection.commit()

    # ==================== USERS ====================

    async def add_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None) -> int:
        """Добавляет нового пользователя."""
        referral_code = f"REF{telegram_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor = await self._connection.execute(
            """INSERT INTO users (telegram_id, username, first_name, last_name, referral_code, referred_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, last_name, referral_code, referred_by)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по telegram_id."""
        cursor = await self._connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по реферальному коду."""
        cursor = await self._connection.execute(
            "SELECT * FROM users WHERE referral_code = ?", (referral_code,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def update_user(self, telegram_id: int, **kwargs) -> None:
        """Обновляет данные пользователя."""
        if not kwargs:
            return
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        await self._connection.execute(
            f"UPDATE users SET {set_clause} WHERE telegram_id = ?", values
        )
        await self._connection.commit()

    # ==================== PRODUCTS ====================

    async def add_product(self, name: str, description: str, price: float, category: str, file_path: str = None, content: str = None) -> int:
        """Добавляет новый товар."""
        cursor = await self._connection.execute(
            """INSERT INTO products (name, description, price, category, file_path, content)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, price, category, file_path, content)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получает товар по ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Получает все активные товары."""
        cursor = await self._connection.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY category, name"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Получает товары по категории."""
        cursor = await self._connection.execute(
            "SELECT * FROM products WHERE category = ? AND is_active = 1", (category,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_categories(self) -> List[str]:
        """Получает список всех категорий."""
        cursor = await self._connection.execute(
            "SELECT DISTINCT category FROM products WHERE is_active = 1"
        )
        rows = await cursor.fetchall()
        return [row['category'] for row in rows if row['category']]

    async def update_product(self, product_id: int, **kwargs) -> None:
        """Обновляет данные товара."""
        if not kwargs:
            return
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        await self._connection.execute(
            f"UPDATE products SET {set_clause} WHERE id = ?", values
        )
        await self._connection.commit()

    async def delete_product(self, product_id: int) -> None:
        """Удаляет товар (мягкое удаление)."""
        await self._connection.execute(
            "UPDATE products SET is_active = 0 WHERE id = ?", (product_id,)
        )
        await self._connection.commit()

    # ==================== ORDERS ====================

    async def create_order(self, user_id: int, product_id: int, quantity: int = 1, payment_method: str = None) -> int:
        """Создает новый заказ."""
        product = await self.get_product(product_id)
        if not product:
            raise ValueError("Товар не найден")

        total_price = product['price'] * quantity
        cursor = await self._connection.execute(
            """INSERT INTO orders (user_id, product_id, quantity, total_price, payment_method)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, product_id, quantity, total_price, payment_method)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получает заказ по ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает все заказы пользователя."""
        cursor = await self._connection.execute(
            """SELECT o.*, p.name as product_name, p.file_path, p.content
               FROM orders o
               JOIN products p ON o.product_id = p.id
               WHERE o.user_id = ? ORDER BY o.created_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_order_status(self, order_id: int, status: str) -> None:
        """Обновляет статус заказа."""
        await self._connection.execute(
            "UPDATE orders SET payment_status = ? WHERE id = ?", (status, order_id)
        )
        await self._connection.commit()

    # ==================== CART ====================

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        """Добавляет товар в корзину."""
        # Проверяем, есть ли уже такой товар в корзине
        cursor = await self._connection.execute(
            "SELECT * FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        existing = await cursor.fetchone()

        if existing:
            await self._connection.execute(
                "UPDATE cart SET quantity = quantity + ? WHERE id = ?",
                (quantity, existing['id'])
            )
        else:
            await self._connection.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity)
            )
        await self._connection.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает корзину пользователя."""
        cursor = await self._connection.execute(
            """SELECT c.*, p.name, p.price, p.description, p.file_path, p.content
               FROM cart c
               JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ? AND p.is_active = 1""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def remove_from_cart(self, user_id: int, product_id: int) -> None:
        """Удаляет товар из корзины."""
        await self._connection.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        await self._connection.commit()

    async def clear_cart(self, user_id: int) -> None:
        """Очищает корзину пользователя."""
        await self._connection.execute(
            "DELETE FROM cart WHERE user_id = ?", (user_id,)
        )
        await self._connection.commit()

    async def get_cart_total(self, user_id: int) -> float:
        """Получает общую стоимость корзины."""
        cart_items = await self.get_cart(user_id)
        return sum(item['price'] * item['quantity'] for item in cart_items)

    # ==================== REFERRAL SYSTEM ====================

    async def add_referral(self, referrer_id: int, referred_user_id: int, reward_amount: float = 0) -> None:
        """Добавляет запись о реферале."""
        await self._connection.execute(
            """INSERT INTO referral_system (referrer_id, referred_user_id, reward_amount)
               VALUES (?, ?, ?)""",
            (referrer_id, referred_user_id, reward_amount)
        )
        await self._connection.commit()

    async def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает всех рефералов пользователя."""
        cursor = await self._connection.execute(
            """SELECT r.*, u.username, u.first_name, u.last_name
               FROM referral_system r
               JOIN users u ON r.referred_user_id = u.telegram_id
               WHERE r.referrer_id = ?""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_referral_count(self, user_id: int) -> int:
        """Получает количество рефералов пользователя."""
        cursor = await self._connection.execute(
            "SELECT COUNT(*) as count FROM referral_system WHERE referrer_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row['count'] if row else 0

    async def get_total_referral_rewards(self, user_id: int) -> float:
        """Получает суммарное вознаграждение за рефералов."""
        cursor = await self._connection.execute(
            "SELECT COALESCE(SUM(reward_amount), 0) as total FROM referral_system WHERE referrer_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row['total'] if row else 0.0

    # ==================== UTILITY ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику для админ-панели."""
        stats = {}

        # Количество пользователей
        cursor = await self._connection.execute("SELECT COUNT(*) as count FROM users")
        row = await cursor.fetchone()
        stats['users'] = row['count'] if row else 0

        # Количество товаров
        cursor = await self._connection.execute("SELECT COUNT(*) as count FROM products WHERE is_active = 1")
        row = await cursor.fetchone()
        stats['products'] = row['count'] if row else 0

        # Количество заказов
        cursor = await self._connection.execute("SELECT COUNT(*) as count FROM orders")
        row = await cursor.fetchone()
        stats['orders'] = row['count'] if row else 0

        # Общая выручка
        cursor = await self._connection.execute(
            "SELECT COALESCE(SUM(total_price), 0) as total FROM orders WHERE payment_status = 'paid'"
        )
        row = await cursor.fetchone()
        stats['revenue'] = row['total'] if row else 0

        return stats


# Создаем глобальный экземпляр базы данных
db = Database()
