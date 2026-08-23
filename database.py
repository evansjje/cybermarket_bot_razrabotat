import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Establish connection and create tables if not exist."""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA foreign_keys = ON")
        await self._create_tables()
        await self.conn.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def _create_tables(self) -> None:
        """Create all necessary tables."""
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0.0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS referral_system (
                referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                reward_amount REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
        """)

    # ========== USER METHODS ==========
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None) -> None:
        """Add new user to database."""
        referral_code = f"REF{user_id}{int(datetime.now().timestamp())}"
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, referral_code, referred_by) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, referral_code, referred_by)
        )
        await self.conn.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        cursor = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    async def update_user_balance(self, user_id: int, amount: float) -> None:
        """Update user balance."""
        await self.conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await self.conn.commit()

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get user by referral code."""
        cursor = await self.conn.execute("SELECT * FROM users WHERE referral_code = ?", (referral_code,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    # ========== PRODUCT METHODS ==========
    async def add_product(self, name: str, description: str, price: float, category: str, file_path: str = None, content: str = None) -> int:
        """Add new product."""
        cursor = await self.conn.execute(
            "INSERT INTO products (name, description, price, category, file_path, content) VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, category, file_path, content)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        cursor = await self.conn.execute("SELECT * FROM products WHERE product_id = ? AND is_active = 1", (product_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all active products."""
        cursor = await self.conn.execute("SELECT * FROM products WHERE is_active = 1")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category."""
        cursor = await self.conn.execute("SELECT * FROM products WHERE category = ? AND is_active = 1", (category,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_categories(self) -> List[str]:
        """Get all unique categories."""
        cursor = await self.conn.execute("SELECT DISTINCT category FROM products WHERE is_active = 1")
        rows = await cursor.fetchall()
        return [row[0] for row in rows if row[0]]

    async def update_product(self, product_id: int, **kwargs) -> None:
        """Update product fields."""
        if not kwargs:
            return
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        await self.conn.execute(f"UPDATE products SET {set_clause} WHERE product_id = ?", values)
        await self.conn.commit()

    async def delete_product(self, product_id: int) -> None:
        """Soft delete product."""
        await self.conn.execute("UPDATE products SET is_active = 0 WHERE product_id = ?", (product_id,))
        await self.conn.commit()

    # ========== CART METHODS ==========
    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> None:
        """Add product to cart."""
        await self.conn.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, quantity)
        )
        await self.conn.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart with product details."""
        cursor = await self.conn.execute("""
            SELECT c.cart_id, c.quantity, p.* 
            FROM cart c 
            JOIN products p ON c.product_id = p.product_id 
            WHERE c.user_id = ? AND p.is_active = 1
        """, (user_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart."""
        await self.conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def remove_from_cart(self, cart_id: int) -> None:
        """Remove item from cart."""
        await self.conn.execute("DELETE FROM cart WHERE cart_id = ?", (cart_id,))
        await self.conn.commit()

    # ========== ORDER METHODS ==========
    async def create_order(self, user_id: int, product_id: int, quantity: int, total_price: float, payment_id: str = None) -> int:
        """Create new order."""
        cursor = await self.conn.execute(
            "INSERT INTO orders (user_id, product_id, quantity, total_price, payment_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, product_id, quantity, total_price, payment_id)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def update_order_status(self, order_id: int, status: str, payment_id: str = None) -> None:
        """Update order status."""
        if payment_id:
            await self.conn.execute(
                "UPDATE orders SET status = ?, payment_id = ? WHERE order_id = ?",
                (status, payment_id, order_id)
            )
        else:
            await self.conn.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        await self.conn.commit()

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all user orders."""
        cursor = await self.conn.execute("""
            SELECT o.*, p.name as product_name, p.file_path, p.content
            FROM orders o 
            JOIN products p ON o.product_id = p.product_id 
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        cursor = await self.conn.execute("""
            SELECT o.*, p.name as product_name, p.file_path, p.content
            FROM orders o 
            JOIN products p ON o.product_id = p.product_id 
            WHERE o.order_id = ?
        """, (order_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    # ========== REFERRAL METHODS ==========
    async def add_referral(self, referrer_id: int, referred_id: int, reward_amount: float) -> None:
        """Add referral record."""
        await self.conn.execute(
            "INSERT INTO referral_system (referrer_id, referred_id, reward_amount) VALUES (?, ?, ?)",
            (referrer_id, referred_id, reward_amount)
        )
        await self.conn.commit()

    async def get_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all referrals for user."""
        cursor = await self.conn.execute("""
            SELECT r.*, u.username, u.first_name, u.last_name
            FROM referral_system r 
            JOIN users u ON r.referred_id = u.user_id 
            WHERE r.referrer_id = ?
        """, (user_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Get referral statistics for user."""
        cursor = await self.conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(reward_amount), 0) as total_reward FROM referral_system WHERE referrer_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return {"count": row[0], "total_reward": row[1]}


# Global database instance
db = Database()
