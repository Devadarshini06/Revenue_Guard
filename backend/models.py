from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    country = Column(String(100), nullable=False, default="United States")
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    customers = relationship("Customer", back_populates="region")
    orders = relationship("Order", back_populates="region")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    target_margin = Column(Float, nullable=False, default=40.0)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    segment = Column(String(50), nullable=False, index=True) # Enterprise, Mid-Market, SMB, Direct Consumer
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    region = relationship("Region", back_populates="customers")
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    order_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="Completed", index=True) # Completed, Refunded, Partially_Refunded, Cancelled
    payment_method = Column(String(50), nullable=False, default="Credit Card") # Credit Card, Wire Transfer, ACH, PayPal
    shipping_cost = Column(Float, default=0.0)
    total_gross_amount = Column(Float, default=0.0)
    total_discount_amount = Column(Float, default=0.0)
    total_refund_amount = Column(Float, default=0.0)
    total_net_amount = Column(Float, default=0.0)

    customer = relationship("Customer", back_populates="orders")
    region = relationship("Region", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    discounts = relationship("Discount", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    gross_revenue = Column(Float, nullable=False) # quantity * unit_price
    net_revenue = Column(Float, nullable=False)   # gross_revenue - discount_amount
    cogs = Column(Float, nullable=False)          # quantity * unit_cost
    profit = Column(Float, nullable=False)        # net_revenue - cogs

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    discounts = relationship("Discount", back_populates="order_item")
    refunds = relationship("Refund", back_populates="order_item")


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True, index=True)
    discount_code = Column(String(50), nullable=True)
    discount_type = Column(String(50), default="Percentage") # Percentage, Fixed, Volume, Promotional
    discount_percentage = Column(Float, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    reason = Column(String(200), nullable=True)

    order = relationship("Order", back_populates="discounts")
    order_item = relationship("OrderItem", back_populates="discounts")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True, index=True)
    refund_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    refund_amount = Column(Float, nullable=False)
    refund_reason = Column(String(100), nullable=False) # Defective Item, Incorrect Product, Late Delivery, Customer Cancellation, Pricing Discrepancy
    status = Column(String(50), default="Approved")

    order = relationship("Order", back_populates="refunds")
    order_item = relationship("OrderItem", back_populates="refunds")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_reference = Column(String(100), unique=True, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False) # Charge, Refund, Adjustment
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(50), default="Settled")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    order = relationship("Order", back_populates="transactions")


class DataUpload(Base):
    __tablename__ = "data_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    rows_count = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    status = Column(String(50), default="Completed") # Completed, Failed, Processing
    upload_date = Column(DateTime, default=datetime.utcnow)
    summary_notes = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="Viewer", index=True) # Super Admin, Admin, Analyst, Viewer
    is_active = Column(Boolean, default=True, nullable=False)
    token_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    replaced_by = Column(String(255), nullable=True)

    user = relationship("User", back_populates="refresh_tokens")

# Add compound indexes for analytical querying performance
Index("idx_orders_date_status", Order.order_date, Order.status)
Index("idx_order_items_product_order", OrderItem.product_id, OrderItem.order_id)

