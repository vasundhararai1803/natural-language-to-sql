"""
Database models and connection setup for QueryLens AI.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///data/querylens.db")

engine = create_engine(
    DB_PATH,
    connect_args={"check_same_thread": False} if DB_PATH.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Region(Base):
    __tablename__ = "regions"

    region_id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(50), nullable=False, unique=True)
    country = Column(String(50), nullable=False)

    transactions = relationship("Transaction", back_populates="region")


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    customer_segment = Column(String(50), nullable=False)  # Enterprise, SMB, Consumer, VIP
    signup_date = Column(DateTime, nullable=False)

    transactions = relationship("Transaction", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # Electronics, Software, Services, Hardware
    subcategory = Column(String(50), nullable=False)

    transactions = relationship("Transaction", back_populates="product")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    transaction_timestamp = Column(DateTime, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    transaction_status = Column(String(30), nullable=False, index=True)  # completed, cancelled, refunded, pending
    payment_method = Column(String(30), nullable=False)  # credit_card, bank_transfer, paypal, crypto
    channel = Column(String(30), nullable=False)  # web, mobile_app, direct_sales, partner

    region = relationship("Region", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")


# Composite indexes for fast analytics filtering & aggregation
Index("idx_tx_status_date", Transaction.transaction_status, Transaction.transaction_timestamp)
Index("idx_tx_prod_date", Transaction.product_id, Transaction.transaction_timestamp)
Index("idx_tx_reg_date", Transaction.region_id, Transaction.transaction_timestamp)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH.replace("sqlite:///", "")), exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
