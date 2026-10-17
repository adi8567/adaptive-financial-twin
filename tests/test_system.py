import pytest
from fastapi.testclient import TestClient
from backend.main import app
from simulation.monte_carlo import MonteCarloSimulator, EconomicRegime
from behavioral_engine.engine import BehavioralEngine, BehavioralConstraintEngine
from rl.environments.financial_env import FinancialTwinEnv, FinancialAction
from rl.policies.policies import TrainedRLPolicy, RuleBasedPolicy, RandomPolicy

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["system"] == "Adaptive Financial Twin"

def test_demo_initialization_and_dashboard():
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "net_worth" in data
    assert data["monthly_income"] == 100000.0
    assert data["debt"] == 300000.0
    assert data["financial_health_score"] > 0

def test_twin_state_and_deterministic_transition():
    # 1. Fetch current twin
    res_twin = client.get("/api/v1/twin")
    assert res_twin.status_code == 200
    initial_cash = res_twin.json()["cash_balance"]

    # 2. Post a deterministic event: salary received of 50,000
    event_payload = {
        "event_type": "salary_received",
        "event_payload": {"amount": 50000.0}
    }
    res_trans = client.post("/api/v1/twin/events", json=event_payload)
    assert res_trans.status_code == 200
    updated_cash = res_trans.json()["cash_balance"]
    assert updated_cash == initial_cash + 50000.0

    # 3. Check event log history
    res_history = client.get("/api/v1/twin/history")
    assert res_history.status_code == 200
    assert len(res_history.json()) >= 1

def test_monte_carlo_statistical_correctness():
    simulator = MonteCarloSimulator(random_seed=42)
    res = simulator.run(
        initial_cash=150000.0,
        initial_investments=500000.0,
        initial_debt=300000.0,
        monthly_income=100000.0,
        monthly_expenses=62000.0,
        debt_emi=14000.0,
        horizon_months=12,
        num_simulations=1000,
        regime=EconomicRegime.NORMAL
    )
    # Check percentile order invariants: p10 <= p50 <= p90
    assert res.p10_net_worth <= res.median_final_net_worth
    assert res.median_final_net_worth <= res.p90_net_worth
    assert 0.0 <= res.goal_achievement_probability <= 1.0
    assert 0.0 <= res.bankruptcy_exhaustion_probability <= 1.0

def test_behavioral_engine_explicit_constraints():
    state = {
        "cash_balance": 80000.0,
        "monthly_expenses": 50000.0,
        "monthly_income": 100000.0,
        "debt_balance": 300000.0,
        "emergency_fund_months": 1.6, # Under 3.0 months
        "risk_tolerance": "medium"
    }
    profile = BehavioralEngine.infer_profile_from_state_and_history("user-test", state, [])
    assert 0.0 <= profile.present_bias.value <= 1.0
    assert profile.present_bias.confidence > 0.0

    constraints = BehavioralConstraintEngine.get_constraints(profile, state)
    rule_names = [c.rule_name for c in constraints]
    assert "EMERGENCY_FUND_SAFETY_LOCK" in rule_names

def test_rl_environment_and_policies():
    env = FinancialTwinEnv()
    obs = env.reset()
    assert len(obs) == 11
    
    # Step environment
    obs, reward, done, _, info = env.step(FinancialAction.BUILD_EMERGENCY_FUND.value)
    assert isinstance(reward, float)
    assert "emergency_fund_months" in info

    # Check Trained Policy action selection
    policy = TrainedRLPolicy()
    act = policy.select_action(obs)
    assert 0 <= act <= 7

def test_recommendation_engine_traceability():
    res = client.get("/api/v1/recommendations")
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) >= 3
    for r in recs:
        assert "action" in r
        assert "reason" in r
        assert "expected_benefit" in r
        assert "behavioral_reason" in r
        assert "simulation_evidence" in r

def test_copilot_affordability_query():
    payload = {
        "query": "Can I afford a car costing ₹8 lakh?",
        "user_id": "alex",
        "current_state": {},
        "scenario": "NORMAL"
    }
    res = client.post("/api/v1/copilot/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "800,000" in data["answer"] or "8 Lakh" in data["answer"]
    assert len(data["citations"]) > 0
    assert data["is_decision_support"] is True
