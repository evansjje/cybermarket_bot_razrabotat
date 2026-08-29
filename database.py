import aiosqlite
from typing import List, Dict, Optional, Any
from config import settings


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Establish database connection"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()
        await self._seed_data()

    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()

    async def _create_tables(self):
        """Create all necessary tables"""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                desc TEXT DEFAULT '',
                price REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.commit()

    async def _seed_data(self):
        """Seed initial data if database is empty"""
        # Check if categories exist
        cursor = await self.db.execute("SELECT COUNT(*) as count FROM categories")
        row = await cursor.fetchone()
        if row['count'] == 0:
            # Add default categories
            categories = [
                ('🎮 Games',),
                ('💻 Software',),
                ('🎵 Media',)
            ]
            await self.db.executemany(
                "INSERT INTO categories (title) VALUES (?)",
                categories
            )
            
            # Get category IDs
            cursor = await self.db.execute("SELECT id, title FROM categories")
            cat_rows = await cursor.fetchall()
            cat_ids = {r['title']: r['id'] for r in cat_rows}
            
            # Add default products
            products = [
                (cat_ids['🎮 Games'], 'Cyberpunk 2077', 'Full game digital key', 59.99),
                (cat_ids['🎮 Games'], 'Elden Ring', 'Digital deluxe edition', 69.99),
                (cat_ids['💻 Software'], 'Windows 11 Pro', 'Digital license key', 129.99),
                (cat_ids['🎵 Media'], 'Spotify Premium', '3 months subscription', 29.99)
            ]
            await self.db.executemany(
                "INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)",
                products
            )
            await self.db.commit()

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        cursor = await self.db.execute("SELECT * FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def add_category(self, title: str) -> int:
        """Add new category"""
        cursor = await self.db.execute(
            "INSERT INTO categories (title) VALUES (?)",
            (title,)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def get_products(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get products, optionally filtered by category"""
        if category_id is not None:
            cursor = await self.db.execute(
                "SELECT * FROM products WHERE category_id = ? ORDER BY id",
                (category_id,)
            )
        else:
            cursor = await self.db.execute("SELECT * FROM products ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get single product by ID"""
        cursor = await self.db.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def add_product(self, category_id: int, title: str, desc: str, price: float) -> int:
        """Add new product"""
        cursor = await self.db.execute(
            "INSERT INTO products (category_id, title, desc, price) VALUES (?, ?, ?, ?)",
            (category_id, title, desc, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_product_price(self, product_id: int, price: float) -> None:
        """Update product price"""
        await self.db.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (price, product_id)
        )
        await self.db.commit()

    async def update_product_desc(self, product_id: int, desc: str) -> None:
        """Update product description"""
        await self.db.execute(
            "UPDATE products SET desc = ? WHERE id = ?",
            (desc, product_id)
        )
        await self.db.commit()

    async def delete_product(self, product_id: int) -> None:
        """Delete product"""
        await self.db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self.db.commit()

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        """Add product to user's cart"""
        # Check if product already in cart
        cursor = await self.db.execute(
            "SELECT id, count FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            # Update count
            await self.db.execute(
                "UPDATE cart SET count = count + 1 WHERE id = ?",
                (existing['id'],)
            )
        else:
            # Insert new
            await self.db.execute(
                "INSERT INTO cart (user_id, product_id, count) VALUES (?, ?, 1)",
                (user_id, product_id)
            )
        await self.db.commit()

    async def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart with product details"""
        cursor = await self.db.execute("""
            SELECT 
                c.id as cart_id,
                c.product_id,
                c.count,
                p.title,
                p.price,
                p.desc
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
            ORDER BY c.id
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_cart(self, user_id: int) -> None:
        """Clear user's cart"""
        await self.db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics for admin panel"""
        # Total users
        cursor = await self.db.execute("SELECT COUNT(*) as count FROM users")
        row = await cursor.fetchone()
        total_users = row['count']
        
        # Total products
        cursor = await self.db.execute("SELECT COUNT(*) as count FROM products")
        row = await cursor.fetchone()
        total_products = row['count']
        
        # Total categories
        cursor = await self.db.execute("SELECT COUNT(*) as count FROM categories")
        row = await cursor.fetchone()
        total_categories = row['count']
        
        # Total cart items
        cursor = await self.db.execute("SELECT COUNT(*) as count FROM cart")
        row = await cursor.fetchone()
        total_cart_items = row['count']
        
        # Total revenue (sum of all prices in cart)
        cursor = await self.db.execute("""
            SELECT SUM(p.price * c.count) as total 
            FROM cart c
            JOIN products p ON c.product_id = p.id
        """)
        row = await cursor.fetchone()
        total_revenue = row['total'] or 0
        
        return {
            'total_users': total_users,
            'total_products': total_products,
            'total_categories': total_categories,
            'total_cart_items': total_cart_items,
            'total_revenue': total_revenue
        }

    async def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> None:
        """Register or update user in database"""
        await self.db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        await self.db.commit()


# Global database instance
db = Database()
