import aiosqlite
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = "cybermarket.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Подключение к базе данных и создание таблиц"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.create_tables()
        await self.seed_data()
        logger.info("База данных подключена")

    async def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.db:
            await self.db.close()
            logger.info("База данных закрыта")

    async def create_tables(self) -> None:
        """Создание всех таблиц"""
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            );
        """)
        await self.db.commit()

    async def seed_data(self) -> None:
        """Авто-заполнение демо-данными"""
        # Проверяем, есть ли уже категории
        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return

        # Демо-категории
        categories = [
            ("🎮 Игры",),
            ("💻 Софт",),
            ("🎁 Подарки",)
        ]
        await self.db.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            categories
        )

        # Демо-товары
        products = [
            (1, "CS:GO Prime", "Премиум-аккаунт CS:GO", 1499.0),
            (1, "Steam Wallet 1000", "Пополнение кошелька Steam на 1000 руб", 950.0),
            (2, "Windows 11 Pro", "Лицензионный ключ Windows 11 Pro", 2999.0),
            (3, "Discord Nitro 1 мес", "Подписка Discord Nitro на 1 месяц", 399.0)
        ]
        await self.db.executemany(
            "INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)",
            products
        )
        await self.db.commit()
        logger.info("Демо-данные добавлены")

    async def add_user(self, user_id: int, username: str = None, first_name: str = None,
                       last_name: str = None, referrer_id: int = None) -> None:
        """Добавление нового пользователя"""
        await self.db.execute(
            """INSERT OR IGNORE INTO users (id, username, first_name, last_name, referrer_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, first_name, last_name, referrer_id)
        )
        await self.db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        cursor = await self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Получение всех категорий"""
        cursor = await self.db.execute("SELECT * FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Получение товаров по категории"""
        cursor = await self.db.execute(
            "SELECT * FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получение товара по ID"""
        cursor = await self.db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Получение всех товаров"""
        cursor = await self.db.execute("SELECT * FROM products ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        """Добавление товара в корзину"""
        await self.db.execute(
            """INSERT INTO cart (user_id, product_id, count)
               VALUES (?, ?, 1)
               ON CONFLICT(user_id, product_id) DO UPDATE SET count = count + 1""",
            (user_id, product_id)
        )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение корзины пользователя с деталями товаров"""
        cursor = await self.db.execute(
            """SELECT c.product_id, c.count, p.name, p.price, p.description
               FROM cart c
               JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ?""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Очистка корзины пользователя"""
        await self.db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def create_order(self, user_id: int, items: List[Dict[str, Any]]) -> int:
        """Создание заказа"""
        total_amount = sum(item['price'] * item['count'] for item in items)

        cursor = await self.db.execute(
            "INSERT INTO orders (user_id, total_amount) VALUES (?, ?)",
            (user_id, total_amount)
        )
        order_id = cursor.lastrowid

        for item in items:
            await self.db.execute(
                """INSERT INTO order_items (order_id, product_id, count, price)
                   VALUES (?, ?, ?, ?)""",
                (order_id, item['product_id'], item['count'], item['price'])
            )

        await self.clear_cart(user_id)
        await self.db.commit()
        return order_id

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получение заказа по ID"""
        cursor = await self.db.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_order_items(self, order_id: int) -> List[Dict[str, Any]]:
        """Получение товаров заказа"""
        cursor = await self.db.execute(
            """SELECT oi.*, p.name
               FROM order_items oi
               JOIN products p ON oi.product_id = p.id
               WHERE oi.order_id = ?""",
            (order_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех заказов пользователя"""
        cursor = await self.db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_stats(self) -> Dict[str, int]:
        """Получение статистики для админ-панели"""
        stats = {}

        cursor = await self.db.execute("SELECT COUNT(*) FROM users")
        stats['users'] = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM products")
        stats['products'] = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM orders")
        stats['orders'] = (await cursor.fetchone())[0]

        cursor = await self.db.execute("SELECT COUNT(*) FROM categories")
        stats['categories'] = (await cursor.fetchone())[0]

        return stats

    async def add_category(self, name: str) -> None:
        """Добавление новой категории"""
        await self.db.execute(
            "INSERT INTO categories (name) VALUES (?)", (name,)
        )
        await self.db.commit()

    async def add_product(self, category_id: int, name: str, description: str, price: float) -> None:
        """Добавление нового товара"""
        await self.db.execute(
            """INSERT INTO products (category_id, name, description, price)
               VALUES (?, ?, ?, ?)""",
            (category_id, name, description, price)
        )
        await self.db.commit()

    async def delete_product(self, product_id: int) -> None:
        """Удаление товара"""
        await self.db.execute(
            "DELETE FROM products WHERE id = ?", (product_id,)
        )
        await self.db.commit()

    async def delete_category(self, category_id: int) -> None:
        """Удаление категории"""
        await self.db.execute(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        await self.db.commit()

    async def get_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение рефералов пользователя"""
        cursor = await self.db.execute(
            "SELECT * FROM users WHERE referrer_id = ?", (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# Создаем глобальный экземпляр базы данных
db = Database()
