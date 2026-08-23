# database.py
import os
import sqlite3
import aiosqlite
from typing import Optional, List, Dict, Any


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
                    referral_code TEXT,
                    referred_by INTEGER,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Products table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT,
                    file_path TEXT,
                    download_link TEXT,
                    is_available INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Orders table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    total_price REAL NOT NULL,
                    payment_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                )
            ''')

            # Referral system table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS referral_system (
                    referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    referred_user_id INTEGER NOT NULL,
                    reward_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_user_id) REFERENCES users (user_id)
                )
            ''')

            await db.commit()

    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referral_code: str = None, referred_by: int = None) -> bool:
        """Add new user to database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user exists
            cursor = await db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            existing = await cursor.fetchone()

            if existing:
                return False

            # Generate referral code if not provided
            if not referral_code:
                referral_code = f"REF{user_id}"

            await db.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, referral_code, referred_by))

            await db.commit()
            return True

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        if not kwargs:
            return False

        async with aiosqlite.connect(self.db_path) as db:
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)

            await db.execute(f'UPDATE users SET {set_clause} WHERE user_id = ?', values)
            await db.commit()
            return True

    async def add_product(self, name: str, description: str, price: float, category: str, file_path: str = None, download_link: str = None) -> int:
        """Add new product to database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO products (name, description, price, category, file_path, download_link)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, price, category, file_path, download_link))

            await db.commit()
            return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_products(self, category: str = None) -> List[Dict[str, Any]]:
        """Get all products, optionally filtered by category"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if category:
                cursor = await db.execute('SELECT * FROM products WHERE category = ? AND is_available = 1', (category,))
            else:
                cursor = await db.execute('SELECT * FROM products WHERE is_available = 1')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product information"""
        if not kwargs:
            return False

        async with aiosqlite.connect(self.db_path) as db:
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(product_id)

            await db.execute(f'UPDATE products SET {set_clause} WHERE product_id = ?', values)
            await db.commit()
            return True

    async def delete_product(self, product_id: int) -> bool:
        """Delete product from database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
            await db.commit()
            return True

    async def get_categories(self) -> List[str]:
        """Get all unique product categories"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT DISTINCT category FROM products WHERE is_available = 1')
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row[0]]

    async def create_order(self, user_id: int, product_id: int, quantity: int = 1, total_price: float = None) -> int:
        """Create new order"""
        if not total_price:
            product = await self.get_product(product_id)
            if not product:
                return 0
            total_price = product['price'] * quantity

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO orders (user_id, product_id, quantity, total_price)
                VALUES (?, ?, ?, ?)
            ''', (user_id, product_id, quantity, total_price))

            await db.commit()
            return cursor.lastrowid

    async def update_order_status(self, order_id: int, status: str, payment_id: str = None) -> bool:
        """Update order status"""
        async with aiosqlite.connect(self.db_path) as db:
            if payment_id:
                await db.execute('UPDATE orders SET status = ?, payment_id = ? WHERE order_id = ?', (status, payment_id, order_id))
            else:
                await db.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))
            await db.commit()
            return True

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT o.*, p.name as product_name, p.price as product_price
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
            ''', (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT o.*, p.name as product_name, p.price as product_price, p.file_path, p.download_link
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                WHERE o.order_id = ?
            ''', (order_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_referral(self, user_id: int, referred_user_id: int, reward_amount: float = 0) -> int:
        """Add referral record"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO referral_system (user_id, referred_user_id, reward_amount)
                VALUES (?, ?, ?)
            ''', (user_id, referred_user_id, reward_amount))

            await db.commit()
            return cursor.lastrowid

    async def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all referrals for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT r.*, u.username, u.first_name, u.last_name
                FROM referral_system r
                JOIN users u ON r.referred_user_id = u.user_id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
            ''', (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Get referral statistics for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total referrals
            cursor = await db.execute('SELECT COUNT(*) FROM referral_system WHERE user_id = ?', (user_id,))
            total_referrals = (await cursor.fetchone())[0]

            # Total rewards
            cursor = await db.execute('SELECT COALESCE(SUM(reward_amount), 0) FROM referral_system WHERE user_id = ?', (user_id,))
            total_rewards = (await cursor.fetchone())[0]

            # Pending rewards
            cursor = await db.execute('SELECT COALESCE(SUM(reward_amount), 0) FROM referral_system WHERE user_id = ? AND status = "pending"', (user_id,))
            pending_rewards = (await cursor.fetchone())[0]

            return {
                'total_referrals': total_referrals,
                'total_rewards': total_rewards,
                'pending_rewards': pending_rewards
            }

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get user by referral code"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users WHERE referral_code = ?', (referral_code,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT o.*, u.username, u.first_name, u.last_name, p.name as product_name
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN products p ON o.product_id = p.product_id
                ORDER BY o.created_at DESC
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total users
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]

            # Total products
            cursor = await db.execute('SELECT COUNT(*) FROM products')
            total_products = (await cursor.fetchone())[0]

            # Total orders
            cursor = await db.execute('SELECT COUNT(*) FROM orders')
            total_orders = (await cursor.fetchone())[0]

            # Total revenue
            cursor = await db.execute('SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE status = "completed"')
            total_revenue = (await cursor.fetchone())[0]

            return {
                'total_users': total_users,
                'total_products': total_products,
                'total_orders': total_orders,
                'total_revenue': total_revenue
            }


# Create global database instance
db = Database()
