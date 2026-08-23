import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Устанавливает соединение с базой данных и создает таблицы"""
        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute("PRAGMA foreign_keys = ON")
        await self.create_tables()

    async def close(self) -> None:
        """Закрывает соединение с базой данных"""
        if self.connection:
            await self.connection.close()

    async def create_tables(self) -> None:
        """Создает все необходимые таблицы"""
        await self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                balance REAL DEFAULT 0.0,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users (id)
            );

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
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS referral_system (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                reward_amount REAL DEFAULT 0.0,
                is_paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id),
                FOREIGN KEY (referred_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                UNIQUE(user_id, product_id)
            );
        """)
        await self.connection.commit()

    # ==================== USER METHODS ====================

    async def add_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None) -> int:
        """Добавляет нового пользователя"""
        referral_code = f"REF{telegram_id}{int(datetime.now().timestamp())}"
        
        cursor = await self.connection.execute(
            """INSERT INTO users (telegram_id, username, first_name, last_name, referral_code, referred_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, last_name, referral_code, referred_by)
        )
        await self.connection.commit()
        
        user_id = cursor.lastrowid
        
        # Если есть реферальный код, создаем запись в referral_system
        if referred_by:
            await self.connection.execute(
                """INSERT INTO referral_system (referrer_id, referred_id)
                   VALUES (?, ?)""",
                (referred_by, user_id)
            )
            await self.connection.commit()
        
        return user_id

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по telegram_id"""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по внутреннему ID"""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по реферальному коду"""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE referral_code = ?",
            (referral_code,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def update_user(self, telegram_id: int, **kwargs) -> None:
        """Обновляет данные пользователя"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(telegram_id)
        
        await self.connection.execute(
            f"UPDATE users SET {set_clause} WHERE telegram_id = ?",
            values
        )
        await self.connection.commit()

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей"""
        cursor = await self.connection.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ==================== PRODUCT METHODS ====================

    async def add_product(self, name: str, description: str, price: float, category: str, file_path: str = None, download_link: str = None) -> int:
        """Добавляет новый товар"""
        cursor = await self.connection.execute(
            """INSERT INTO products (name, description, price, category, file_path, download_link)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, price, category, file_path, download_link)
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получает товар по ID"""
        cursor = await self.connection.execute(
            "SELECT * FROM products WHERE id = ? AND is_active = 1",
            (product_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def get_all_products(self, category: str = None) -> List[Dict[str, Any]]:
        """Получает все активные товары, опционально по категории"""
        if category:
            cursor = await self.connection.execute(
                "SELECT * FROM products WHERE is_active = 1 AND category = ?",
                (category,)
            )
        else:
            cursor = await self.connection.execute(
                "SELECT * FROM products WHERE is_active = 1"
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_categories(self) -> List[str]:
        """Получает все уникальные категории товаров"""
        cursor = await self.connection.execute(
            "SELECT DISTINCT category FROM products WHERE is_active = 1"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def update_product(self, product_id: int, **kwargs) -> None:
        """Обновляет данные товара"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(product_id)
        
        await self.connection.execute(
            f"UPDATE products SET {set_clause} WHERE id = ?",
            values
        )
        await self.connection.commit()

    async def delete_product(self, product_id: int) -> None:
        """Удаляет товар (мягкое удаление)"""
        await self.connection.execute(
            "UPDATE products SET is_active = 0 WHERE id = ?",
            (product_id,)
        )
        await self.connection.commit()

    # ==================== CART METHODS ====================

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        """Добавляет товар в корзину"""
        await self.connection.execute(
            """INSERT OR REPLACE INTO cart (user_id, product_id, quantity)
               VALUES (?, ?, ?)""",
            (user_id, product_id, quantity)
        )
        await self.connection.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает корзину пользователя"""
        cursor = await self.connection.execute(
            """SELECT c.*, p.name, p.price, p.description, p.category
               FROM cart c
               JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ? AND p.is_active = 1""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def remove_from_cart(self, user_id: int, product_id: int) -> None:
        """Удаляет товар из корзины"""
        await self.connection.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        await self.connection.commit()

    async def clear_cart(self, user_id: int) -> None:
        """Очищает корзину пользователя"""
        await self.connection.execute(
            "DELETE FROM cart WHERE user_id = ?",
            (user_id,)
        )
        await self.connection.commit()

    async def get_cart_total(self, user_id: int) -> float:
        """Получает общую сумму корзины"""
        cursor = await self.connection.execute(
            """SELECT SUM(c.quantity * p.price) as total
               FROM cart c
               JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ? AND p.is_active = 1""",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] else 0.0

    # ==================== ORDER METHODS ====================

    async def create_order(self, user_id: int, product_id: int, quantity: int, total_price: float, payment_method: str = None, payment_id: str = None) -> int:
        """Создает новый заказ"""
        cursor = await self.connection.execute(
            """INSERT INTO orders (user_id, product_id, quantity, total_price, payment_method, payment_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, product_id, quantity, total_price, payment_method, payment_id)
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получает заказ по ID"""
        cursor = await self.connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает все заказы пользователя"""
        cursor = await self.connection.execute(
            """SELECT o.*, p.name as product_name, p.file_path, p.download_link
               FROM orders o
               JOIN products p ON o.product_id = p.id
               WHERE o.user_id = ?
               ORDER BY o.created_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_order_status(self, order_id: int, status: str) -> None:
        """Обновляет статус заказа"""
        await self.connection.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )
        await self.connection.commit()

    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """Получает все заказы"""
        cursor = await self.connection.execute(
            """SELECT o.*, u.telegram_id, u.username, p.name as product_name
               FROM orders o
               JOIN users u ON o.user_id = u.id
               JOIN products p ON o.product_id = p.id
               ORDER BY o.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ==================== REFERRAL METHODS ====================

    async def get_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает всех рефералов пользователя"""
        cursor = await self.connection.execute(
            """SELECT rs.*, u.telegram_id, u.username, u.first_name, u.last_name
               FROM referral_system rs
               JOIN users u ON rs.referred_id = u.id
               WHERE rs.referrer_id = ?""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику реферальной программы"""
        cursor = await self.connection.execute(
            """SELECT COUNT(*) as total_referrals,
                      SUM(CASE WHEN is_paid = 1 THEN reward_amount ELSE 0 END) as total_earned,
                      SUM(CASE WHEN is_paid = 0 THEN reward_amount ELSE 0 END) as pending_earned
               FROM referral_system
               WHERE referrer_id = ?""",
            (user_id,)
        )
        row = await cursor.fetchone()
        return {
            "total_referrals": row[0] if row else 0,
            "total_earned": row[1] if row and row[1] else 0.0,
            "pending_earned": row[2] if row and row[2] else 0.0
        }

    async def add_referral_reward(self, referrer_id: int, referred_id: int, reward_amount: float) -> None:
        """Добавляет вознаграждение за реферала"""
        await self.connection.execute(
            """UPDATE referral_system
               SET reward_amount = ?
               WHERE referrer_id = ? AND referred_id = ?""",
            (reward_amount, referrer_id, referred_id)
        )
        await self.connection.commit()

    async def mark_referral_paid(self, referral_id: int) -> None:
        """Отмечает реферальное вознаграждение как выплаченное"""
        await self.connection.execute(
            "UPDATE referral_system SET is_paid = 1 WHERE id = ?",
            (referral_id,)
        )
        await self.connection.commit()

    # ==================== BALANCE METHODS ====================

    async def add_balance(self, user_id: int, amount: float) -> None:
        """Добавляет баланс пользователю"""
        await self.connection.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?",
            (amount, user_id)
        )
        await self.connection.commit()

    async def deduct_balance(self, user_id: int, amount: float) -> bool:
        """Списывает баланс пользователя"""
        user = await self.get_user_by_id(user_id)
        if user and user['balance'] >= amount:
            await self.connection.execute(
                "UPDATE users SET balance = balance - ? WHERE id = ?",
                (amount, user_id)
            )
            await self.connection.commit()
            return True
        return False


# Глобальный экземпляр базы данных
db = Database()
