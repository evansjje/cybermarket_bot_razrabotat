import os
import sqlite3
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "data/cybermarket.db"):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    async def init_db(self) -> None:
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0.0,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referred_by) REFERENCES users (user_id)
                )
            ''')

            # Products table
            await db.execute('''
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
                )
            ''')

            # Orders table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    payment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            # Referral system table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS referral_system (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    referred_user_id INTEGER NOT NULL,
                    reward REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_user_id) REFERENCES users (user_id)
                )
            ''')

            await db.commit()

    # User methods
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None) -> None:
        """Add new user to database"""
        async with aiosqlite.connect(self.db_path) as db:
            referral_code = f"REF{user_id}{int(datetime.now().timestamp())}"
            await db.execute(
                'INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, referral_code, referred_by) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, username, first_name, last_name, referral_code, referred_by)
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'balance': row[4],
                    'referral_code': row[5],
                    'referred_by': row[6],
                    'created_at': row[7]
                }
            return None

    async def update_user_balance(self, user_id: int, amount: float) -> None:
        """Update user balance"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            await db.commit()

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get user by referral code"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM users WHERE referral_code = ?', (referral_code,))
            row = await cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'balance': row[4],
                    'referral_code': row[5],
                    'referred_by': row[6],
                    'created_at': row[7]
                }
            return None

    # Product methods
    async def add_product(self, name: str, description: str, price: float, category: str, file_path: str = None, content: str = None) -> int:
        """Add new product"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'INSERT INTO products (name, description, price, category, file_path, content) VALUES (?, ?, ?, ?, ?, ?)',
                (name, description, price, category, file_path, content)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (product_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': row[3],
                    'category': row[4],
                    'file_path': row[5],
                    'content': row[6],
                    'is_active': row[7],
                    'created_at': row[8]
                }
            return None

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all active products"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC')
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': row[3],
                    'category': row[4],
                    'file_path': row[5],
                    'content': row[6],
                    'is_active': row[7],
                    'created_at': row[8]
                }
                for row in rows
            ]

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY created_at DESC',
                (category,)
            )
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': row[3],
                    'category': row[4],
                    'file_path': row[5],
                    'content': row[6],
                    'is_active': row[7],
                    'created_at': row[8]
                }
                for row in rows
            ]

    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT DISTINCT category FROM products WHERE is_active = 1')
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row[0]]

    async def update_product(self, product_id: int, **kwargs) -> None:
        """Update product"""
        async with aiosqlite.connect(self.db_path) as db:
            allowed_fields = ['name', 'description', 'price', 'category', 'file_path', 'content', 'is_active']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if updates:
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values())
                values.append(product_id)
                await db.execute(f'UPDATE products SET {set_clause} WHERE id = ?', values)
                await db.commit()

    async def delete_product(self, product_id: int) -> None:
        """Soft delete product"""
        await self.update_product(product_id, is_active=0)

    # Order methods
    async def create_order(self, user_id: int, product_id: int, amount: float, payment_method: str = 'yookassa') -> int:
        """Create new order"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'INSERT INTO orders (user_id, product_id, amount, payment_method) VALUES (?, ?, ?, ?)',
                (user_id, product_id, amount, payment_method)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_order_status(self, order_id: int, status: str, payment_id: str = None) -> None:
        """Update order status"""
        async with aiosqlite.connect(self.db_path) as db:
            if payment_id:
                await db.execute(
                    'UPDATE orders SET status = ?, payment_id = ? WHERE id = ?',
                    (status, payment_id, order_id)
                )
            else:
                await db.execute(
                    'UPDATE orders SET status = ? WHERE id = ?',
                    (status, order_id)
                )
            await db.commit()

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'product_id': row[2],
                    'amount': row[3],
                    'status': row[4],
                    'payment_method': row[5],
                    'payment_id': row[6],
                    'created_at': row[7]
                }
            return None

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all orders for user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'product_id': row[2],
                    'amount': row[3],
                    'status': row[4],
                    'payment_method': row[5],
                    'payment_id': row[6],
                    'created_at': row[7]
                }
                for row in rows
            ]

    async def get_paid_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get paid orders for user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM orders WHERE user_id = ? AND status = "paid" ORDER BY created_at DESC',
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'product_id': row[2],
                    'amount': row[3],
                    'status': row[4],
                    'payment_method': row[5],
                    'payment_id': row[6],
                    'created_at': row[7]
                }
                for row in rows
            ]

    # Referral methods
    async def add_referral(self, user_id: int, referred_user_id: int, reward: float = 0.0) -> None:
        """Add referral record"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO referral_system (user_id, referred_user_id, reward) VALUES (?, ?, ?)',
                (user_id, referred_user_id, reward)
            )
            await db.commit()

    async def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all referrals for user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM referral_system WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'referred_user_id': row[2],
                    'reward': row[3],
                    'status': row[4],
                    'created_at': row[5]
                }
                for row in rows
            ]

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Get referral statistics for user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT COUNT(*), COALESCE(SUM(reward), 0) FROM referral_system WHERE user_id = ? AND status = "completed"',
                (user_id,)
            )
            row = await cursor.fetchone()
            return {
                'total_referrals': row[0] if row else 0,
                'total_rewards': row[1] if row else 0.0
            }

    async def update_referral_status(self, referral_id: int, status: str) -> None:
        """Update referral status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE referral_system SET status = ? WHERE id = ?',
                (status, referral_id)
            )
            await db.commit()


# Global database instance
db = Database()
