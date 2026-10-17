from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.models.financial import (
    AccountType, TransactionType, AssetType, LiabilityType, GoalPriority, GoalCategory
)

# ================= AUTH SCHEMAS =================
class UserBase(BaseModel):
    email: str
    full_name: str
    age: int = 27
    location: str = "Mumbai, India"
    employment_status: str = "Salaried Professional"
    income_sources: List[Dict[str, Any]] = []
    financial_preferences: Dict[str, Any] = {}
    risk_tolerance: str = "medium"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ================= ACCOUNT SCHEMAS =================
class AccountBase(BaseModel):
    name: str
    account_type: AccountType
    account_number_masked: str
    currency: str = "INR"
    current_balance: float = 0.0
    is_active: bool = True

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ================= TRANSACTION SCHEMAS =================
class TransactionBase(BaseModel):
    account_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    amount: float
    merchant: str
    category: str
    transaction_type: TransactionType
    is_recurring: bool = False
    confidence_score: float = 1.0
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# ================= ASSET SCHEMAS =================
class AssetBase(BaseModel):
    name: str
    asset_type: AssetType
    current_value: float
    expected_return_rate: float = 0.08
    volatility: float = 0.15
    liquidity_score: float = 1.0

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ================= LIABILITY SCHEMAS =================
class LiabilityBase(BaseModel):
    name: str
    liability_type: LiabilityType
    total_principal: float
    remaining_principal: float
    interest_rate: float
    monthly_emi: float
    tenure_months_remaining: int

class LiabilityCreate(LiabilityBase):
    pass

class LiabilityResponse(LiabilityBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ================= GOAL SCHEMAS =================
class GoalBase(BaseModel):
    name: str
    category: GoalCategory = GoalCategory.CUSTOM
    target_amount: float
    current_amount: float = 0.0
    deadline: datetime
    priority: GoalPriority = GoalPriority.MEDIUM
    required_monthly_contribution: float = 0.0
    probability_of_success: float = 0.5
    is_completed: bool = False

class GoalCreate(GoalBase):
    pass

class GoalResponse(GoalBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ================= FINANCIAL TWIN & SNAPSHOT SCHEMAS =================
class FinancialStateSchema(BaseModel):
    cash_balance: float
    monthly_income: float
    monthly_expenses: float
    savings_rate: float
    debt_balance: float
    investment_value: float
    net_worth: float
    emergency_fund_months: float
    goal_progress: float
    risk_tolerance: str
    income_stability: float
    expense_volatility: float
    financial_stress_score: float
    behavioral_profile: Dict[str, Any]
    timestamp: datetime
    version: int = 1

class EventCreate(BaseModel):
    event_type: str
    event_payload: Dict[str, Any]
    timestamp: Optional[datetime] = None

class EventResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    event_payload: Dict[str, Any]
    timestamp: datetime
    version: int

    class Config:
        from_attributes = True

# ================= DASHBOARD SUMMARY SCHEMAS =================
class DashboardSummary(BaseModel):
    net_worth: float
    monthly_income: float
    monthly_expenses: float
    savings_rate: float
    debt: float
    emergency_fund_months: float
    goal_progress: float
    cash_flow: float
    financial_health_score: float
    timestamp: datetime
