from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.models.financial import (
    User, Account, Transaction, Asset, Liability, Goal, FinancialSnapshot, EventLog,
    AccountType, TransactionType, AssetType, LiabilityType, GoalPriority, GoalCategory
)
from backend.app.core.security import get_password_hash
from backend.app.services.twin_service import FinancialTwinService

def seed_demo_data(db: Session) -> User:
    """
    Creates the canonical demo persona 'Alex' (27 y/o) as specified in the prompt:
    Monthly Income: ₹100,000
    Expenses: ₹62,000
    Emergency Fund: ₹150,000
    Investments: ₹500,000
    Debt: ₹300,000
    Goal: ₹1,000,000 house down payment
    Risk Tolerance: Medium
    Behavior: Present bias high (0.76), Loss aversion medium (0.55), Discipline medium (0.68)
    Explicitly labeled as DEMO DATA.
    """
    alex = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if alex:
        return alex

    # 1. Create User
    alex = User(
        email="alex.demo@financialtwin.internal",
        hashed_password=get_password_hash("demo_password_123!"),
        full_name="Alex (Simulated Persona - DEMO DATA)",
        age=27,
        location="Bengaluru, India",
        employment_status="Senior Software Engineer",
        income_sources=[
            {"name": "Primary Engineering Salary (DEMO)", "amount": 100000.0, "frequency": "monthly"}
        ],
        financial_preferences={
            "currency": "INR",
            "is_demo_account": True,
            "target_retirement_age": 55
        },
        risk_tolerance="medium"
    )
    db.add(alex)
    db.commit()
    db.refresh(alex)

    # 2. Create Accounts
    salary_acc = Account(
        user_id=alex.id,
        name="HDFC Salary Account (DEMO)",
        account_type=AccountType.BANK_ACCOUNT.value,
        account_number_masked="****-****-8821",
        current_balance=150000.0,  # Represents emergency cash fund
        is_active=True
    )
    cc_acc = Account(
        user_id=alex.id,
        name="Axis Neo Credit Card (DEMO)",
        account_type=AccountType.CREDIT_CARD.value,
        account_number_masked="****-****-4309",
        current_balance=0.0,
        is_active=True
    )
    db.add_all([salary_acc, cc_acc])
    db.commit()
    db.refresh(salary_acc)

    # 3. Create Assets
    mf_asset = Asset(
        user_id=alex.id,
        name="Nifty 50 Index Mutual Fund (DEMO)",
        asset_type=AssetType.MUTUAL_FUNDS.value,
        current_value=350000.0,
        expected_return_rate=0.12,
        volatility=0.16,
        liquidity_score=0.9
    )
    stock_asset = Asset(
        user_id=alex.id,
        name="Large Cap Direct Equities (DEMO)",
        asset_type=AssetType.STOCKS.value,
        current_value=150000.0,
        expected_return_rate=0.14,
        volatility=0.22,
        liquidity_score=0.95
    )
    db.add_all([mf_asset, stock_asset])
    db.commit()

    # 4. Create Liabilities
    car_loan = Liability(
        user_id=alex.id,
        name="Auto Loan (DEMO)",
        liability_type=LiabilityType.LOAN.value,
        total_principal=500000.0,
        remaining_principal=300000.0,
        interest_rate=0.095, # 9.5% interest
        monthly_emi=14000.0,
        tenure_months_remaining=24
    )
    db.add(car_loan)
    db.commit()

    # 5. Create Goals
    house_goal = Goal(
        user_id=alex.id,
        name="House Down Payment (DEMO)",
        category=GoalCategory.HOUSE.value,
        target_amount=1000000.0,
        current_amount=250000.0,
        deadline=datetime.now(timezone.utc) + timedelta(days=365 * 3), # 3 years out
        priority=GoalPriority.HIGH.value,
        required_monthly_contribution=20800.0,
        probability_of_success=0.74,
        is_completed=False
    )
    db.add(house_goal)
    db.commit()

    # 6. Seed Historical Transactions (Last 3 months)
    now = datetime.now(timezone.utc)
    demo_txs = [
        Transaction(
            user_id=alex.id,
            account_id=salary_acc.id,
            timestamp=now - timedelta(days=28),
            amount=100000.0,
            merchant="TechCorp Global Payroll",
            category="Salary",
            transaction_type=TransactionType.INCOME.value,
            is_recurring=True,
            confidence_score=1.0,
            notes="DEMO DATA: Monthly salary credit"
        ),
        Transaction(
            user_id=alex.id,
            account_id=salary_acc.id,
            timestamp=now - timedelta(days=26),
            amount=28000.0,
            merchant="Bengaluru Urban Rentals",
            category="Rent & Housing",
            transaction_type=TransactionType.EXPENSE.value,
            is_recurring=True,
            confidence_score=1.0,
            notes="DEMO DATA: Monthly apartment rent"
        ),
        Transaction(
            user_id=alex.id,
            account_id=salary_acc.id,
            timestamp=now - timedelta(days=25),
            amount=14000.0,
            merchant="HDFC Auto Finance",
            category="Loan EMI",
            transaction_type=TransactionType.DEBT_PAYMENT.value,
            is_recurring=True,
            confidence_score=1.0,
            notes="DEMO DATA: Car loan EMI"
        ),
        Transaction(
            user_id=alex.id,
            account_id=salary_acc.id,
            timestamp=now - timedelta(days=20),
            amount=12000.0,
            merchant="Nature Basket & Fresh Groceries",
            category="Groceries & Essentials",
            transaction_type=TransactionType.EXPENSE.value,
            is_recurring=False,
            confidence_score=0.98,
            notes="DEMO DATA: Groceries"
        ),
        Transaction(
            user_id=alex.id,
            account_id=salary_acc.id,
            timestamp=now - timedelta(days=12),
            amount=8000.0,
            merchant="Dining & Weekend Leisure",
            category="Discretionary & Dining",
            transaction_type=TransactionType.EXPENSE.value,
            is_recurring=False,
            confidence_score=0.95,
            notes="DEMO DATA: Dining & entertainment"
        )
    ]
    db.add_all(demo_txs)
    db.commit()

    # 7. Initial State Transition and Baseline Snapshot
    state = FinancialTwinService.calculate_current_state(db, alex.id)
    snapshot = FinancialSnapshot(
        user_id=alex.id,
        version=1,
        cash_balance=state.cash_balance,
        monthly_income=state.monthly_income,
        monthly_expenses=state.monthly_expenses,
        savings_rate=state.savings_rate,
        debt_balance=state.debt_balance,
        investment_value=state.investment_value,
        net_worth=state.net_worth,
        emergency_fund_months=state.emergency_fund_months,
        goal_progress=state.goal_progress,
        risk_tolerance=state.risk_tolerance,
        income_stability=state.income_stability,
        expense_volatility=state.expense_volatility,
        financial_stress_score=state.financial_stress_score,
        behavioral_profile=state.behavioral_profile,
        timestamp=now
    )
    db.add(snapshot)

    # Initial Event
    event = EventLog(
        user_id=alex.id,
        event_type="genesis_snapshot",
        event_payload={"description": "Initial digital twin genesis for Alex (DEMO DATA)"},
        version=1,
        timestamp=now
    )
    db.add(event)
    db.commit()

    return alex
