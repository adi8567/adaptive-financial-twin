import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base
import enum

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class AccountType(str, enum.Enum):
    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    INVESTMENT_ACCOUNT = "investment_account"
    LOAN_ACCOUNT = "loan_account"

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    INVESTMENT = "investment"
    DEBT_PAYMENT = "debt_payment"
    TRANSFER = "transfer"

class AssetType(str, enum.Enum):
    CASH = "cash"
    STOCKS = "stocks"
    MUTUAL_FUNDS = "mutual_funds"
    BONDS = "bonds"
    OTHER = "other"

class LiabilityType(str, enum.Enum):
    LOAN = "loan"
    CREDIT_CARD = "credit_card"
    EMI = "emi"
    OTHER = "other"

class GoalPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class GoalCategory(str, enum.Enum):
    EMERGENCY_FUND = "emergency_fund"
    HOUSE = "house"
    CAR = "car"
    EDUCATION = "education"
    RETIREMENT = "retirement"
    CUSTOM = "custom"

# ==================== ORM MODELS ====================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer, default=27)
    location = Column(String, default="Mumbai, India")
    employment_status = Column(String, default="Salaried Professional")
    income_sources = Column(JSON, default=list) # e.g. [{"name": "Tech Corp Salary", "amount": 100000, "frequency": "monthly"}]
    financial_preferences = Column(JSON, default=dict)
    risk_tolerance = Column(String, default="medium") # low, medium, high
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="user", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    snapshots = relationship("FinancialSnapshot", back_populates="user", cascade="all, delete-orphan")
    events = relationship("EventLog", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False) # AccountType
    account_number_masked = Column(String, nullable=False) # e.g. ****-****-1234
    currency = Column(String, default="INR")
    current_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
    amount = Column(Float, nullable=False) # Positive value
    merchant = Column(String, nullable=False)
    category = Column(String, nullable=False) # groceries, rent, utilities, discretionary, etc.
    transaction_type = Column(String, nullable=False) # TransactionType
    is_recurring = Column(Boolean, default=False)
    confidence_score = Column(Float, default=1.0) # Categorization / parsing confidence
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False) # AssetType
    current_value = Column(Float, default=0.0)
    expected_return_rate = Column(Float, default=0.08) # 8% annual expected
    volatility = Column(Float, default=0.15) # 15% annual stdev
    liquidity_score = Column(Float, default=1.0) # 0 to 1
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="assets")

class Liability(Base):
    __tablename__ = "liabilities"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    liability_type = Column(String, nullable=False) # LiabilityType
    total_principal = Column(Float, nullable=False)
    remaining_principal = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False) # Annual interest rate (e.g. 0.09 for 9%)
    monthly_emi = Column(Float, default=0.0)
    tenure_months_remaining = Column(Integer, default=12)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="liabilities")

class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="custom") # GoalCategory
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    deadline = Column(DateTime, nullable=False)
    priority = Column(String, default="medium") # GoalPriority
    required_monthly_contribution = Column(Float, default=0.0)
    probability_of_success = Column(Float, default=0.5) # Computed deterministically or by MC
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="goals")

class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False) # salary_received, expense, investment, etc.
    event_payload = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utc_now, index=True)
    version = Column(Integer, default=1)
    checksum = Column(String, nullable=True)

    user = relationship("User", back_populates="events")

class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
    version = Column(Integer, default=1)
    
    # Financial State Metrics
    cash_balance = Column(Float, default=0.0)
    monthly_income = Column(Float, default=0.0)
    monthly_expenses = Column(Float, default=0.0)
    savings_rate = Column(Float, default=0.0)
    debt_balance = Column(Float, default=0.0)
    investment_value = Column(Float, default=0.0)
    net_worth = Column(Float, default=0.0)
    emergency_fund_months = Column(Float, default=0.0)
    goal_progress = Column(Float, default=0.0)
    
    # Behavioral and risk metrics
    risk_tolerance = Column(String, default="medium")
    income_stability = Column(Float, default=0.9)
    expense_volatility = Column(Float, default=0.15)
    financial_stress_score = Column(Float, default=25.0) # 0 to 100
    behavioral_profile = Column(JSON, default=dict)

    user = relationship("User", back_populates="snapshots")
