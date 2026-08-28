from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CRYPTO = "crypto"
    CARD = "card"
    SBP = "sbp"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """User model representing a Telegram user."""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    referral_code: Optional[str] = None
    referred_by: Optional[int] = None
    balance: float = 0.0
    total_purchases: float = 0.0
    is_admin: bool = False
    is_blocked: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert User to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by,
            'balance': self.balance,
            'total_purchases': self.total_purchases,
            'is_admin': int(self.is_admin),
            'is_blocked': int(self.is_blocked),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary."""
        return cls(
            id=data['id'],
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            referral_code=data.get('referral_code'),
            referred_by=data.get('referred_by'),
            balance=data.get('balance', 0.0),
            total_purchases=data.get('total_purchases', 0.0),
            is_admin=bool(data.get('is_admin', 0)),
            is_blocked=bool(data.get('is_blocked', 0)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            last_activity=datetime.fromisoformat(data['last_activity']) if data.get('last_activity') else datetime.now()
        )


@dataclass
class Category:
    """Category model for product categorization."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Category to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'is_active': int(self.is_active),
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """Create Category from dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            icon=data.get('icon'),
            is_active=bool(data.get('is_active', 1)),
            sort_order=data.get('sort_order', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class Product:
    """Product model for digital goods."""
    id: Optional[int] = None
    category_id: int = 0
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    old_price: Optional[float] = None
    photo_url: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    stock: int = 0
    sold_count: int = 0
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Product to dictionary."""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'old_price': self.old_price,
            'photo_url': self.photo_url,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'is_active': int(self.is_active),
            'is_featured': int(self.is_featured),
            'stock': self.stock,
            'sold_count': self.sold_count,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create Product from dictionary."""
        return cls(
            id=data.get('id'),
            category_id=data.get('category_id', 0),
            name=data.get('name', ''),
            description=data.get('description'),
            price=data.get('price', 0.0),
            old_price=data.get('old_price'),
            photo_url=data.get('photo_url'),
            file_path=data.get('file_path'),
            file_type=data.get('file_type'),
            is_active=bool(data.get('is_active', 1)),
            is_featured=bool(data.get('is_featured', 0)),
            stock=data.get('stock', 0),
            sold_count=data.get('sold_count', 0),
            sort_order=data.get('sort_order', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


@dataclass
class CartItem:
    """Cart item model."""
    id: Optional[int] = None
    user_id: int = 0
    product_id: int = 0
    quantity: int = 1
    price: float = 0.0
    added_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CartItem to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'added_at': self.added_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CartItem':
        """Create CartItem from dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            product_id=data.get('product_id', 0),
            quantity=data.get('quantity', 1),
            price=data.get('price', 0.0),
            added_at=datetime.fromisoformat(data['added_at']) if data.get('added_at') else datetime.now()
        )


@dataclass
class Order:
    """Order model."""
    id: Optional[int] = None
    user_id: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)
    total_amount: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_details: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Order to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': self.items,
            'total_amount': self.total_amount,
            'status': self.status.value,
            'payment_method': self.payment_method.value if self.payment_method else None,
            'payment_details': self.payment_details,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create Order from dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            items=data.get('items', []),
            total_amount=data.get('total_amount', 0.0),
            status=OrderStatus(data.get('status', 'pending')),
            payment_method=PaymentMethod(data['payment_method']) if data.get('payment_method') else None,
            payment_details=data.get('payment_details'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        )


@dataclass
class Review:
    """Review model."""
    id: Optional[int] = None
    user_id: int = 0
    product_id: int = 0
    rating: int = 5
    text: Optional[str] = None
    is_approved: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Review to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'rating': self.rating,
            'text': self.text,
            'is_approved': int(self.is_approved),
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """Create Review from dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            product_id=data.get('product_id', 0),
            rating=data.get('rating', 5),
            text=data.get('text'),
            is_approved=bool(data.get('is_approved', 0)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class SupportTicket:
    """Support ticket model."""
    id: Optional[int] = None
    user_id: int = 0
    subject: str = ""
    message: str = ""
    status: str = "open"
    admin_response: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert SupportTicket to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'admin_response': self.admin_response,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupportTicket':
        """Create SupportTicket from dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            subject=data.get('subject', ''),
            message=data.get('message', ''),
            status=data.get('status', 'open'),
            admin_response=data.get('admin_response'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            closed_at=datetime.fromisoformat(data['closed_at']) if data.get('closed_at') else None
        )


@dataclass
class Referral:
    """Referral model."""
    id: Optional[int] = None
    referrer_id: int = 0
    referred_id: int = 0
    bonus_amount: float = 0.0
    is_paid: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Referral to dictionary."""
        return {
            'id': self.id,
            'referrer_id': self.referrer_id,
            'referred_id': self.referred_id,
            'bonus_amount': self.bonus_amount,
            'is_paid': int(self.is_paid),
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Referral':
        """Create Referral from dictionary."""
        return cls(
            id=data.get('id'),
            referrer_id=data.get('referrer_id', 0),
            referred_id=data.get('referred_id', 0),
            bonus_amount=data.get('bonus_amount', 0.0),
            is_paid=bool(data.get('is_paid', 0)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class Payment:
    """Payment model."""
    id: Optional[int] = None
    order_id: int = 0
    user_id: int = 0
    amount: float = 0.0
    method: PaymentMethod = PaymentMethod.CRYPTO
    status: str = "pending"
    transaction_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    paid_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Payment to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'method': self.method.value,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'details': self.details,
            'created_at': self.created_at.isoformat(),
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Payment':
        """Create Payment from dictionary."""
        return cls(
            id=data.get('id'),
            order_id=data.get('order_id', 0),
            user_id=data.get('user_id', 0),
            amount=data.get('amount', 0.0),
            method=PaymentMethod(data['method']) if data.get('method') else PaymentMethod.CRYPTO,
            status=data.get('status', 'pending'),
            transaction_id=data.get('transaction_id'),
            details=data.get('details'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            paid_at=datetime.fromisoformat(data['paid_at']) if data.get('paid_at') else None
        )


@dataclass
class AdminLog:
    """Admin action log model."""
    id: Optional[int] = None
    admin_id: int = 0
    action: str = ""
    details: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AdminLog to dictionary."""
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdminLog':
        """Create AdminLog from dictionary."""
        return cls(
            id=data.get('id'),
            admin_id=data.get('admin_id', 0),
            action=data.get('action', ''),
            details=data.get('details'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class Settings:
    """Bot settings model."""
    id: Optional[int] = None
    key: str = ""
    value: Any = None
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Settings to dictionary."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create Settings from dictionary."""
        return cls(
            id=data.get('id'),
            key=data.get('key', ''),
            value=data.get('value'),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


# Database table schemas
TABLES = {
    'users': """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            balance REAL DEFAULT 0,
            total_purchases REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_activity TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'categories': """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'products': """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL DEFAULT 0,
            old_price REAL,
            photo_url TEXT,
            file_path TEXT,
            file_type TEXT,
            is_active INTEGER DEFAULT 1,
            is_featured INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 0,
            sold_count INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    """,
    'cart_items': """
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    """,
    'orders': """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """,
    'reviews': """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER DEFAULT 5,
            text TEXT,
            is_approved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    """,
    'support_tickets': """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            admin_response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            closed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """,
    'referrals': """
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            bonus_amount REAL DEFAULT 0,
            is_paid INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (referred_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """,
    'payments': """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            method TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            transaction_id TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            paid_at TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """,
    'admin_logs': """
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """,
    'settings': """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
}
