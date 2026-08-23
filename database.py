import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Database:
    def __init__(self, db_path: str = "cybermarket.db"):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Create database connection and tables"""
        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute("PRAGMA foreign_keys = ON")
        await self._create_tables()
        await self.connection.commit()

    async def close(self) -> None:
        """Close database connection"""
        if self.connection:
            await self.connection.close()

    async def _create_tables(self) -> None:
        """Create all necessary tables"""
        await self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                registration_date TEXT,
                is_admin INTEGER DEFAULT 0,
                balance REAL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                file_path TEXT,
                download_link TEXT,
                is_available INTEGER DEFAULT 1,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                payment_id TEXT,
                created_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );

            CREATE TABLE IF NOT EXISTS referral_system (
                referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_user_id INTEGER NOT NULL,
                reward_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_user_id) REFERENCES users (user_id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                rating INTEGER DEFAULT 5,
                review_text TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );

            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id);
        """)

    # ==================== USER METHODS ====================

    async def add_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        referred_by: Optional[int] = None
    ) -> None:
        """Add new user to database"""
        referral_code = f"REF{user_id}{int(datetime.now().timestamp())}"
        registration_date = datetime.now().isoformat()

        await self.connection.execute(
            """INSERT OR IGNORE INTO users 
            (user_id, username, first_name, last_name, referral_code, referred_by, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username, first_name, last_name, referral_code, referred_by, registration_date)
        )
        await self.connection.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = ["user_id", "username", "first_name", "last_name", 
                      "referral_code", "referred_by", "registration_date", 
                      "is_admin", "balance"]
            return dict(zip(columns, row))
        return None

    async def update_user_balance(self, user_id: int, amount: float) -> None:
        """Update user balance"""
        await self.connection.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await self.connection.commit()

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get user by referral code"""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE referral_code = ?", (referral_code,)
        )
        row = await cursor.fetchone()
        if row:
            columns = ["user_id", "username", "first_name", "last_name", 
                      "referral_code", "referred_by", "registration_date", 
                      "is_admin", "balance"]
            return dict(zip(columns, row))
        return None

    # ==================== PRODUCT METHODS ====================

    async def add_product(
        self,
        name: str,
        description: str,
        price: float,
        category: str,
        file_path: Optional[str] = None,
        download_link: Optional[str] = None
    ) -> int:
        """Add new product"""
        created_at = datetime.now().isoformat()
        cursor = await self.connection.execute(
            """INSERT INTO products 
            (name, description, price, category, file_path, download_link, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, description, price, category, file_path, download_link, created_at)
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        cursor = await self.connection.execute(
            "SELECT * FROM products WHERE product_id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = ["product_id", "name", "description", "price", "category",
                      "file_path", "download_link", "is_available", "created_at"]
            return dict(zip(columns, row))
        return None

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all available products"""
        cursor = await self.connection.execute(
            "SELECT * FROM products WHERE is_available = 1 ORDER BY category, name"
        )
        rows = await cursor.fetchall()
        columns = ["product_id", "name", "description", "price", "category",
                  "file_path", "download_link", "is_available", "created_at"]
        return [dict(zip(columns, row)) for row in rows]

    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category"""
        cursor = await self.connection.execute(
            "SELECT * FROM products WHERE category = ? AND is_available = 1",
            (category,)
        )
        rows = await cursor.fetchall()
        columns = ["product_id", "name", "description", "price", "category",
                  "file_path", "download_link", "is_available", "created_at"]
        return [dict(zip(columns, row)) for row in rows]

    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        cursor = await self.connection.execute(
            "SELECT DISTINCT category FROM products WHERE is_available = 1"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows if row[0]]

    async def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        category: Optional[str] = None,
        file_path: Optional[str] = None,
        download_link: Optional[str] = None,
        is_available: Optional[int] = None
    ) -> None:
        """Update product information"""
        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if price is not None:
            updates.append("price = ?")
            values.append(price)
        if category is not None:
            updates.append("category = ?")
            values.append(category)
        if file_path is not None:
            updates.append("file_path = ?")
            values.append(file_path)
        if download_link is not None:
            updates.append("download_link = ?")
            values.append(download_link)
        if is_available is not None:
            updates.append("is_available = ?")
            values.append(is_available)

        if updates:
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
            await self.connection.execute(query, values)
            await self.connection.commit()

    async def delete_product(self, product_id: int) -> None:
        """Delete product"""
        await self.connection.execute(
            "DELETE FROM products WHERE product_id = ?", (product_id,)
        )
        await self.connection.commit()

    # ==================== ORDER METHODS ====================

    async def create_order(
        self,
        user_id: int,
        product_id: int,
        amount: float,
        payment_method: str = "yookassa"
    ) -> int:
        """Create new order"""
        created_at = datetime.now().isoformat()
        cursor = await self.connection.execute(
            """INSERT INTO orders 
            (user_id, product_id, amount, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (user_id, product_id, amount, payment_method, created_at)
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def update_order_status(
        self,
        order_id: int,
        status: str,
        payment_id: Optional[str] = None
    ) -> None:
        """Update order status"""
        completed_at = datetime.now().isoformat() if status == "completed" else None
        await self.connection.execute(
            """UPDATE orders 
            SET status = ?, payment_id = ?, completed_at = ?
            WHERE order_id = ?""",
            (status, payment_id, completed_at, order_id)
        )
        await self.connection.commit()

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a user"""
        cursor = await self.connection.execute(
            """SELECT o.*, p.name as product_name, p.file_path, p.download_link
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        columns = ["order_id", "user_id", "product_id", "amount", "status",
                  "payment_method", "payment_id", "created_at", "completed_at",
                  "product_name", "file_path", "download_link"]
        return [dict(zip(columns, row)) for row in rows]

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        cursor = await self.connection.execute(
            """SELECT o.*, p.name as product_name, p.file_path, p.download_link
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.order_id = ?""",
            (order_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = ["order_id", "user_id", "product_id", "amount", "status",
                      "payment_method", "payment_id", "created_at", "completed_at",
                      "product_name", "file_path", "download_link"]
            return dict(zip(columns, row))
        return None

    # ==================== CART METHODS ====================

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        """Add product to user's cart"""
        added_at = datetime.now().isoformat()
        await self.connection.execute(
            """INSERT OR IGNORE INTO cart (user_id, product_id, added_at)
            VALUES (?, ?, ?)""",
            (user_id, product_id, added_at)
        )
        await self.connection.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart with product details"""
        cursor = await self.connection.execute(
            """SELECT c.cart_id, c.product_id, c.quantity, c.added_at,
                   p.name, p.price, p.description, p.category
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ? AND p.is_available = 1
            ORDER BY c.added_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        columns = ["cart_id", "product_id", "quantity", "added_at",
                  "name", "price", "description", "category"]
        return [dict(zip(columns, row)) for row in rows]

    async def remove_from_cart(self, cart_id: int) -> None:
        """Remove item from cart"""
        await self.connection.execute(
            "DELETE FROM cart WHERE cart_id = ?", (cart_id,)
        )
        await self.connection.commit()

    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart"""
        await self.connection.execute(
            "DELETE FROM cart WHERE user_id = ?", (user_id,)
        )
        await self.connection.commit()

    # ==================== REFERRAL METHODS ====================

    async def add_referral(
        self,
        referrer_id: int,
        referred_user_id: int,
        reward_amount: float = 0.0
    ) -> None:
        """Add referral record"""
        created_at = datetime.now().isoformat()
        await self.connection.execute(
            """INSERT INTO referral_system 
            (referrer_id, referred_user_id, reward_amount, created_at)
            VALUES (?, ?, ?, ?)""",
            (referrer_id, referred_user_id, reward_amount, created_at)
        )
        await self.connection.commit()

    async def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all referrals for a user"""
        cursor = await self.connection.execute(
            """SELECT r.*, u.username, u.first_name, u.last_name
            FROM referral_system r
            JOIN users u ON r.referred_user_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.created_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        columns = ["referral_id", "referrer_id", "referred_user_id", "reward_amount",
                  "status", "created_at", "username", "first_name", "last_name"]
        return [dict(zip(columns, row)) for row in rows]

    async def update_referral_status(self, referral_id: int, status: str) -> None:
        """Update referral status"""
        await self.connection.execute(
            "UPDATE referral_system SET status = ? WHERE referral_id = ?",
            (status, referral_id)
        )
        await self.connection.commit()

    # ==================== REVIEW METHODS ====================

    async def add_review(
        self,
        user_id: int,
        product_id: int,
        rating: int,
        review_text: Optional[str] = None
    ) -> None:
        """Add product review"""
        created_at = datetime.now().isoformat()
        await self.connection.execute(
            """INSERT INTO reviews (user_id, product_id, rating, review_text, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (user_id, product_id, rating, review_text, created_at)
        )
        await self.connection.commit()

    async def get_product_reviews(self, product_id: int) -> List[Dict[str, Any]]:
        """Get all reviews for a product"""
        cursor = await self.connection.execute(
            """SELECT r.*, u.username, u.first_name
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC""",
            (product_id,)
        )
        rows = await cursor.fetchall()
        columns = ["review_id", "user_id", "product_id", "rating", "review_text",
                  "created_at", "username", "first_name"]
        return [dict(zip(columns, row)) for row in rows]

    # ==================== STATISTICS METHODS ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        stats = {}

        # Total users
        cursor = await self.connection.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        stats["total_users"] = row[0] if row else 0

        # Total products
        cursor = await self.connection.execute("SELECT COUNT(*) FROM products WHERE is_available = 1")
        row = await cursor.fetchone()
        stats["total_products"] = row[0] if row else 0

        # Total orders
        cursor = await self.connection.execute("SELECT COUNT(*) FROM orders")
        row = await cursor.fetchone()
        stats["total_orders"] = row[0] if row else 0

        # Total revenue
        cursor = await self.connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status = 'completed'"
        )
        row = await cursor.fetchone()
        stats["total_revenue"] = row[0] if row else 0.0

        # Today's orders
        today = datetime.now().date().isoformat()
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM orders WHERE date(created_at) = ?", (today,)
        )
        row = await cursor.fetchone()
        stats["today_orders"] = row[0] if row else 0

        return stats


# Global database instance
db = Database()
