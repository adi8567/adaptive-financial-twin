from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.app.db.session import get_db
from backend.app.models.financial import (
    User, Account, Transaction, Asset, Liability, Goal, FinancialSnapshot, EventLog
)
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.schemas.financial import (
    UserResponse, AccountResponse, TransactionResponse, AssetResponse,
    LiabilityResponse, GoalResponse, FinancialStateSchema, EventCreate,
    EventResponse, DashboardSummary, UserCreate, UserLogin, TokenResponse
)
from backend.app.services.twin_service import FinancialTwinService
from backend.app.services.demo_seed import seed_demo_data
from simulation.monte_carlo import MonteCarloSimulator, EconomicRegime, SimulationResult
from behavioral_engine.engine import BehavioralEngine, BehavioralProfile
from recommendation_engine.engine import RecommendationEngine, Recommendation
from llm.copilot import LLMCopilotService, CopilotQueryRequest, CopilotResponse
from rl.policies.policies import evaluate_policies

router = APIRouter()

# ================= 0. AUTHENTICATION (STORE CREDS IN DB) =================
@router.post("/auth/register", response_model=TokenResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        age=user_in.age,
        location=user_in.location,
        employment_status=user_in.employment_status,
        income_sources=user_in.income_sources or [{"name": "Primary Salary", "amount": 100000.0, "frequency": "monthly"}],
        financial_preferences={"currency": "INR"},
        risk_tolerance=user_in.risk_tolerance
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize starter checking account
    starter_acc = Account(
        user_id=new_user.id,
        name="Primary Checking",
        account_type="bank_account",
        account_number_masked="****-****-1092",
        current_balance=250000.0,
        is_active=True
    )
    starter_asset = Asset(
        user_id=new_user.id,
        name="Index Mutual Fund",
        asset_type="mutual_funds",
        current_value=400000.0,
        expected_return_rate=0.12,
        volatility=0.15,
        liquidity_score=0.9
    )
    starter_debt = Liability(
        user_id=new_user.id,
        name="Personal / Auto Loan",
        liability_type="loan",
        total_principal=400000.0,
        remaining_principal=280000.0,
        interest_rate=0.095,
        monthly_emi=13500.0,
        tenure_months_remaining=24
    )
    starter_goal = Goal(
        user_id=new_user.id,
        name="House Down Payment",
        category="house",
        target_amount=1000000.0,
        current_amount=250000.0,
        deadline=datetime.now(timezone.utc),
        priority="high",
        required_monthly_contribution=20000.0,
        probability_of_success=0.74
    )
    db.add_all([starter_acc, starter_asset, starter_debt, starter_goal])
    db.commit()

    token = create_access_token(new_user.id)
    return TokenResponse(
        access_token=token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "age": new_user.age,
            "location": new_user.location,
            "risk_tolerance": new_user.risk_tolerance
        }
    )

@router.post("/auth/login", response_model=TokenResponse)
def login_user(creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password credentials")

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "age": user.age,
            "location": user.location,
            "risk_tolerance": user.risk_tolerance
        }
    )

# ================= 1. DEMO INITIALIZATION =================
@router.post("/demo/init", response_model=UserResponse)
def initialize_demo_persona(db: Session = Depends(get_db)):
    """Initialize canonical demo persona Alex with baseline ledger (DEMO DATA)."""
    alex = seed_demo_data(db)
    return alex

@router.get("/demo/status")
def get_demo_status(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    return {
        "status": "ready",
        "demo_user_id": user.id,
        "demo_user_name": user.full_name,
        "is_demo_mode": True
    }

# ================= 2. DASHBOARD SUMMARY =================
@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    
    state = FinancialTwinService.calculate_current_state(db, user.id)
    cash_flow = state.monthly_income - state.monthly_expenses
    health_score = max(0.0, min(100.0, 100.0 - state.financial_stress_score))

    return DashboardSummary(
        net_worth=state.net_worth,
        monthly_income=state.monthly_income,
        monthly_expenses=state.monthly_expenses,
        savings_rate=state.savings_rate,
        debt=state.debt_balance,
        emergency_fund_months=state.emergency_fund_months,
        goal_progress=state.goal_progress,
        cash_flow=cash_flow,
        financial_health_score=round(health_score, 1),
        timestamp=state.timestamp
    )

# ================= 3. FINANCIAL TWIN STATE & EVENTS =================
@router.get("/twin", response_model=FinancialStateSchema)
def get_financial_twin(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    return FinancialTwinService.calculate_current_state(db, user.id)

@router.get("/twin/history", response_model=List[EventResponse])
def get_twin_history(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    events = (
        db.query(EventLog)
        .filter(EventLog.user_id == user.id)
        .order_by(EventLog.version.asc())
        .all()
    )
    return events

@router.post("/twin/events", response_model=FinancialStateSchema)
def post_twin_event(event_in: EventCreate, db: Session = Depends(get_db)):
    """Apply a deterministic state transition to the financial twin."""
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    return FinancialTwinService.apply_event_transition(
        db, user.id, event_in.event_type, event_in.event_payload
    )

# ================= 4. MONTE CARLO SIMULATION =================
@router.post("/simulation/run", response_model=SimulationResult)
def run_simulation(
    regime: str = "NORMAL",
    num_simulations: int = 10000,
    horizon_months: int = 36,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    state = FinancialTwinService.calculate_current_state(db, user.id)

    regime_enum = getattr(EconomicRegime, regime.upper(), EconomicRegime.NORMAL)
    simulator = MonteCarloSimulator(random_seed=42)
    result = simulator.run(
        initial_cash=state.cash_balance,
        initial_investments=state.investment_value,
        initial_debt=state.debt_balance,
        monthly_income=state.monthly_income,
        monthly_expenses=state.monthly_expenses,
        debt_emi=14000.0,
        goal_target=1000000.0,
        goal_current=250000.0,
        horizon_months=horizon_months,
        num_simulations=num_simulations,
        regime=regime_enum
    )
    return result

# ================= 5. BEHAVIORAL PROFILE =================
@router.get("/behavioral/profile")
def get_behavioral_profile(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    state = FinancialTwinService.calculate_current_state(db, user.id)
    profile = BehavioralEngine.infer_profile_from_state_and_history(
        user.id, state.model_dump(), []
    )
    return profile

# ================= 6. RL POLICY BENCHMARK =================
@router.get("/rl/benchmark")
def get_rl_benchmark():
    """Benchmarking Rule-based vs Random vs Trained RL policy in Gymnasium environment."""
    return evaluate_policies(episodes=30)

# ================= 7. ADAPTIVE RECOMMENDATIONS =================
@router.get("/recommendations", response_model=List[Recommendation])
def get_recommendations(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    state = FinancialTwinService.calculate_current_state(db, user.id)
    engine = RecommendationEngine()
    return engine.generate_recommendations(user.id, state.model_dump(), [])

# ================= 8. WHAT-IF TIME MACHINE =================
@router.post("/what-if/compare")
def compare_what_if_scenarios(
    params_a: Optional[Dict[str, Any]] = None,
    params_b: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Compare Current Plan vs Alternative Plan side-by-side using Monte Carlo.
    Example: Plan A (Buy car) vs Plan B (Delay car by 12 mo and increase SIP).
    """
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    state = FinancialTwinService.calculate_current_state(db, user.id)

    simulator = MonteCarloSimulator(random_seed=42)

    # Baseline Plan A (Buy car next year: add 16,000 EMI, subtract 160,000 cash down payment)
    res_a = simulator.run(
        initial_cash=max(10000.0, state.cash_balance - 160000.0),
        initial_investments=state.investment_value,
        initial_debt=state.debt_balance + 640000.0,
        monthly_income=state.monthly_income,
        monthly_expenses=state.monthly_expenses + 16000.0,
        debt_emi=30000.0,
        goal_target=1000000.0,
        goal_current=250000.0,
        horizon_months=36,
        num_simulations=5000,
        regime=EconomicRegime.NORMAL
    )

    # Alternative Plan B (Delay car by 12 months, increase monthly SIP by 8,000)
    res_b = simulator.run(
        initial_cash=state.cash_balance,
        initial_investments=state.investment_value,
        initial_debt=state.debt_balance,
        monthly_income=state.monthly_income,
        monthly_expenses=state.monthly_expenses,
        debt_emi=14000.0,
        goal_target=1000000.0,
        goal_current=250000.0 + 96000.0, # SIP boost
        horizon_months=36,
        num_simulations=5000,
        regime=EconomicRegime.NORMAL
    )

    return {
        "plan_a": {
            "name": "Plan A: Immediate Car Purchase (₹8 Lakh)",
            "goal_achievement_probability": res_a.goal_achievement_probability,
            "median_net_worth": res_a.median_final_net_worth,
            "cash_resilience_p10": res_a.p10_cash_balance,
            "bankruptcy_risk": res_a.bankruptcy_exhaustion_probability,
            "emergency_adequacy": res_a.emergency_fund_adequacy_rate
        },
        "plan_b": {
            "name": "Plan B: Delay Car 12 Months + Boost SIP ₹8,000/mo",
            "goal_achievement_probability": res_b.goal_achievement_probability,
            "median_net_worth": res_b.median_final_net_worth,
            "cash_resilience_p10": res_b.p10_cash_balance,
            "bankruptcy_risk": res_b.bankruptcy_exhaustion_probability,
            "emergency_adequacy": res_b.emergency_fund_adequacy_rate
        },
        "delta": {
            "goal_success_boost_pct": round((res_b.goal_achievement_probability - res_a.goal_achievement_probability) * 100, 1),
            "median_wealth_advantage": round(res_b.median_final_net_worth - res_a.median_final_net_worth, 2),
            "bankruptcy_risk_reduction_pct": round((res_a.bankruptcy_exhaustion_probability - res_b.bankruptcy_exhaustion_probability) * 100, 1)
        }
    }

# ================= 9. AI COPILOT QUERY =================
@router.post("/copilot/chat", response_model=CopilotResponse)
def copilot_chat(req: CopilotQueryRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "alex.demo@financialtwin.internal").first()
    if not user:
        user = seed_demo_data(db)
    state = FinancialTwinService.calculate_current_state(db, user.id)
    req.current_state = state.model_dump()
    return LLMCopilotService.process_query(req)
