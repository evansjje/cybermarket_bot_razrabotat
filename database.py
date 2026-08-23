import aiosqlite
from typing import List, Optional, Dict, Any
from datetime import datetime

DB_PATH = "cybermarket.db"


async def get_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db() -> None:
    conn = await get_connection()
    try:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referrer_id INTEGER DEFAULT 0,
                balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT NOT NULL,
                price REAL NOT NULL,
                file_data TEXT,
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
                product_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        """)

        # Проверяем и заполняем демо-данные
        async with conn.execute("SELECT COUNT(*) FROM categories") as cursor:
            categories_count = (await cursor.fetchone())[0]

        if categories_count == 0:
            demo_categories = [
                ("Скрипты",),
                ("Курсы",),
                ("Софт",)
            ]
            await conn.executemany(
                "INSERT INTO categories (name) VALUES (?)",
                demo_categories
            )

        async with conn.execute("SELECT COUNT(*) FROM products") as cursor:
            products_count = (await cursor.fetchone())[0]

        if products_count == 0:
            demo_products = [
                (1, "Скрипт автопостинга", "Автоматический постинг в Telegram", 499.0, "https://example.com/script1"),
                (1, "Скрипт парсинга", "Парсинг данных с сайтов", 799.0, "https://example.com/script2"),
                (2, "Курс по Python", "Полный курс по Python с нуля", 1999.0, "https://example.com/course1"),
                (3, "Антивирус Pro", "Профессиональная защита компьютера", 1499.0, "https://example.com/soft1")
            ]
            await conn.executemany(
                """INSERT INTO products (category_id, title, desc, price, file_data)
                   VALUES (?, ?, ?, ?, ?)""",
                demo_products
            )

        await conn.commit()
    finally:
        await conn.close()


async def add_user(user_id: int, username: str = "", first_name: str = "", last_name: str = "", referrer_id: int = 0) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            """INSERT OR IGNORE INTO users (id, username, first_name, last_name, referrer_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, first_name, last_name, referrer_id)
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    finally:
        await conn.close()


async def get_categories() -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute("SELECT * FROM categories ORDER BY id") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_products_by_category(category_id: int) -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute(
            "SELECT * FROM products WHERE category_id = ? ORDER BY id",
            (category_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    finally:
        await conn.close()


async def add_to_cart(user_id: int, product_id: int, count: int = 1) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            """INSERT INTO cart (user_id, product_id, count)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, product_id) DO UPDATE SET count = count + ?""",
            (user_id, product_id, count, count)
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_cart(user_id: int) -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute(
            """SELECT c.product_id, c.count, p.title, p.price, p.desc, p.file_data
               FROM cart c
               JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ?""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await conn.close()


async def update_cart_count(user_id: int, product_id: int, count: int) -> None:
    conn = await get_connection()
    try:
        if count <= 0:
            await conn.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
        else:
            await conn.execute(
                "UPDATE cart SET count = ? WHERE user_id = ? AND product_id = ?",
                (count, user_id, product_id)
            )
        await conn.commit()
    finally:
        await conn.close()


async def clear_cart(user_id: int) -> None:
    conn = await get_connection()
    try:
        await conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await conn.commit()
    finally:
        await conn.close()


async def create_order(user_id: int, product_id: int, count: int, total_price: float) -> int:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """INSERT INTO orders (user_id, product_id, count, total_price)
               VALUES (?, ?, ?, ?)""",
            (user_id, product_id, count, total_price)
        )
        await conn.commit()
        return cursor.lastrowid
    finally:
        await conn.close()


async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute(
            """SELECT o.*, p.title as product_title
               FROM orders o
               JOIN products p ON o.product_id = p.id
               WHERE o.user_id = ?
               ORDER BY o.created_at DESC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_all_orders() -> List[Dict[str, Any]]:
    conn = await get_connection()
    try:
        async with conn.execute(
            """SELECT o.*, u.username, u.first_name, p.title as product_title
               FROM orders o
               JOIN users u ON o.user_id = u.id
               JOIN products p ON o.product_id = p.id
               ORDER BY o.created_at DESC"""
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_stats() -> Dict[str, int]:
    conn = await get_connection()
    try:
        async with conn.execute("SELECT COUNT(*) as count FROM users") as cursor:
            users_count = (await cursor.fetchone())["count"]
        async with conn.execute("SELECT COUNT(*) as count FROM orders") as cursor:
            orders_count = (await cursor.fetchone())["count"]
        async with conn.execute("SELECT COUNT(*) as count FROM products") as cursor:
            products_count = (await cursor.fetchone())["count"]
        return {
            "users": users_count,
            "orders": orders_count,
            "products": products_count
        }
    finally:
        await conn.close()


async def add_product(category_id: int, title: str, desc: str, price: float, file_data: str = "") -> int:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """INSERT INTO products (category_id, title, desc, price, file_data)
               VALUES (?, ?, ?, ?, ?)""",
            (category_id, title, desc, price, file_data)
        )
        await conn.commit()
        return cursor.lastrowid
    finally:
        await conn.close()


async def update_user_balance(user_id: int, amount: float) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?",
            (amount, user_id)
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_referral_stats(user_id: int) -> Dict[str, Any]:
    conn = await get_connection()
    try:
        async with conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE referrer_id = ?",
            (user_id,)
        ) as cursor:
            referrals_count = (await cursor.fetchone())["count"]
        async with conn.execute(
            "SELECT balance FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            balance = row["balance"] if row else 0.0
        return {"referrals": referrals_count, "balance": balance}
    finally:
        await conn.close()
