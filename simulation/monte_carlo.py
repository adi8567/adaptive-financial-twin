import numpy as np
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import enum

class EconomicRegime(str, enum.Enum):
    NORMAL = "NORMAL"
    HIGH_INFLATION = "HIGH_INFLATION"
    RECESSION = "RECESSION"
    BULL_MARKET = "BULL_MARKET"
    BEAR_MARKET = "BEAR_MARKET"
    JOB_LOSS = "JOB_LOSS"
    MEDICAL_EXPENSE = "MEDICAL_EXPENSE"
    COMBINED_STRESS = "COMBINED_STRESS"

# Macroeconomic parameter calibrations for regimes
REGIME_PARAMETERS = {
    EconomicRegime.NORMAL: {
        "inflation_mean": 0.05, "inflation_vol": 0.015,
        "market_return_mean": 0.12, "market_vol": 0.16,
        "income_growth_mean": 0.07, "income_growth_vol": 0.02,
        "monthly_job_loss_prob": 0.005, "job_loss_duration_months": 3,
        "shock_prob": 0.02, "shock_mean": 25000.0
    },
    EconomicRegime.HIGH_INFLATION: {
        "inflation_mean": 0.10, "inflation_vol": 0.03,
        "market_return_mean": 0.06, "market_vol": 0.20,
        "income_growth_mean": 0.04, "income_growth_vol": 0.02,
        "monthly_job_loss_prob": 0.01, "job_loss_duration_months": 4,
        "shock_prob": 0.04, "shock_mean": 40000.0
    },
    EconomicRegime.RECESSION: {
        "inflation_mean": 0.03, "inflation_vol": 0.02,
        "market_return_mean": -0.08, "market_vol": 0.28,
        "income_growth_mean": -0.02, "income_growth_vol": 0.03,
        "monthly_job_loss_prob": 0.04, "job_loss_duration_months": 6,
        "shock_prob": 0.05, "shock_mean": 50000.0
    },
    EconomicRegime.BULL_MARKET: {
        "inflation_mean": 0.04, "inflation_vol": 0.01,
        "market_return_mean": 0.22, "market_vol": 0.14,
        "income_growth_mean": 0.10, "income_growth_vol": 0.02,
        "monthly_job_loss_prob": 0.002, "job_loss_duration_months": 2,
        "shock_prob": 0.015, "shock_mean": 20000.0
    },
    EconomicRegime.BEAR_MARKET: {
        "inflation_mean": 0.06, "inflation_vol": 0.02,
        "market_return_mean": -0.15, "market_vol": 0.32,
        "income_growth_mean": 0.02, "income_growth_vol": 0.02,
        "monthly_job_loss_prob": 0.02, "job_loss_duration_months": 5,
        "shock_prob": 0.03, "shock_mean": 35000.0
    },
    EconomicRegime.JOB_LOSS: {
        "inflation_mean": 0.05, "inflation_vol": 0.015,
        "market_return_mean": 0.08, "market_vol": 0.18,
        "income_growth_mean": 0.00, "income_growth_vol": 0.02,
        "monthly_job_loss_prob": 0.25, "job_loss_duration_months": 6,
        "shock_prob": 0.03, "shock_mean": 30000.0
    },
    EconomicRegime.MEDICAL_EXPENSE: {
        "inflation_mean": 0.06, "inflation_vol": 0.02,
        "market_return_mean": 0.10, "market_vol": 0.16,
        "income_growth_mean": 0.05, "income_growth_vol": 0.02,
        "monthly_job_loss_prob": 0.01, "job_loss_duration_months": 3,
        "shock_prob": 0.20, "shock_mean": 200000.0 # Large medical shock
    },
    EconomicRegime.COMBINED_STRESS: {
        "inflation_mean": 0.11, "inflation_vol": 0.04,
        "market_return_mean": -0.18, "market_vol": 0.35,
        "income_growth_mean": -0.05, "income_growth_vol": 0.04,
        "monthly_job_loss_prob": 0.08, "job_loss_duration_months": 7,
        "shock_prob": 0.12, "shock_mean": 150000.0
    }
}

class SimulationResult(BaseModel):
    regime: str
    num_simulations: int
    horizon_months: int
    median_final_net_worth: float
    p10_net_worth: float
    p90_net_worth: float
    median_cash_balance: float
    p10_cash_balance: float
    p90_cash_balance: float
    bankruptcy_exhaustion_probability: float
    goal_achievement_probability: float
    median_goal_completion_month: Optional[int]
    emergency_fund_adequacy_rate: float
    net_worth_trajectories: List[List[float]] # Sample trajectories for charting
    cash_trajectories: List[List[float]]
    percentile_curve_net_worth: Dict[str, List[float]] # p10, p50, p90 series
    percentile_curve_cash: Dict[str, List[float]]

class MonteCarloSimulator:
    def __init__(self, random_seed: Optional[int] = 42):
        self.random_seed = random_seed

    def run(
        self,
        initial_cash: float,
        initial_investments: float,
        initial_debt: float,
        monthly_income: float,
        monthly_expenses: float,
        debt_emi: float,
        goal_target: float = 1000000.0,
        goal_current: float = 250000.0,
        horizon_months: int = 36,
        num_simulations: int = 10000,
        regime: EconomicRegime = EconomicRegime.NORMAL
    ) -> SimulationResult:
        """
        Executes a vectorized high-dimension Monte Carlo simulation across N stochastic paths.
        All calculations are strictly labeled as SCENARIO ESTIMATES, NOT REAL-FUTURE PREDICTIONS.
        """
        if self.random_seed is not None:
            np.random.seed(self.random_seed)

        params = REGIME_PARAMETERS.get(regime, REGIME_PARAMETERS[EconomicRegime.NORMAL])

        # Vectorized array initialization: shape (num_simulations, horizon_months + 1)
        cash = np.zeros((num_simulations, horizon_months + 1), dtype=np.float64)
        investments = np.zeros((num_simulations, horizon_months + 1), dtype=np.float64)
        debt = np.zeros((num_simulations, horizon_months + 1), dtype=np.float64)
        net_worth = np.zeros((num_simulations, horizon_months + 1), dtype=np.float64)
        goal_accum = np.zeros((num_simulations, horizon_months + 1), dtype=np.float64)

        cash[:, 0] = initial_cash
        investments[:, 0] = initial_investments
        debt[:, 0] = initial_debt
        goal_accum[:, 0] = goal_current
        net_worth[:, 0] = (cash[:, 0] + investments[:, 0]) - debt[:, 0]

        monthly_rf_mean = params["market_return_mean"] / 12.0
        monthly_rf_vol = params["market_vol"] / np.sqrt(12.0)
        monthly_inf_mean = params["inflation_mean"] / 12.0

        # State tracking for job loss durations per path
        unemployed_remaining = np.zeros(num_simulations, dtype=np.int32)
        goal_achieved_month = np.full(num_simulations, fill_value=999, dtype=np.int32)

        for m in range(1, horizon_months + 1):
            # 1. Labor market shocks
            job_loss_events = (np.random.rand(num_simulations) < params["monthly_job_loss_prob"]) & (unemployed_remaining == 0)
            unemployed_remaining[job_loss_events] = params["job_loss_duration_months"]
            
            # Active income calculation (0 if unemployed, otherwise scaled by inflation)
            is_employed = (unemployed_remaining == 0)
            unemployed_remaining[unemployed_remaining > 0] -= 1
            cur_income = np.where(is_employed, monthly_income * ((1.0 + monthly_inf_mean) ** m), 0.0)

            # 2. Expenses subjected to stochastic inflation and random unexpected shocks
            cur_expenses = monthly_expenses * ((1.0 + monthly_inf_mean) ** m)
            shocks = (np.random.rand(num_simulations) < params["shock_prob"]) * np.random.exponential(
                scale=params["shock_mean"], size=num_simulations
            )

            # 3. Market returns (Geometric Brownian Motion sample)
            m_returns = np.random.normal(loc=monthly_rf_mean, scale=monthly_rf_vol, size=num_simulations)
            investments[:, m] = np.maximum(0.0, investments[:, m - 1] * (1.0 + m_returns))

            # 4. Debt amortization
            debt[:, m] = np.maximum(0.0, debt[:, m - 1] - (debt_emi * 0.75)) # Principal reduction approx

            # 5. Cash balance evolution
            active_emi = np.where(debt[:, m - 1] > 0, debt_emi, 0.0)
            net_monthly_flow = cur_income - (cur_expenses + shocks + active_emi)
            
            # Rebalance / goal allocation if surplus
            surplus = np.maximum(0.0, net_monthly_flow)
            deficit = np.maximum(0.0, -net_monthly_flow)

            # 40% surplus to investments, 35% to house goal, 25% to cash reserve
            investments[:, m] += surplus * 0.40
            goal_accum[:, m] = goal_accum[:, m - 1] + (surplus * 0.35)
            cash[:, m] = cash[:, m - 1] + (surplus * 0.25) - deficit

            # If cash deficit, liquidate investments if possible
            liquidate = np.maximum(0.0, -cash[:, m])
            can_liquidate = np.minimum(liquidate, investments[:, m])
            investments[:, m] -= can_liquidate
            cash[:, m] += can_liquidate

            # Track goal completion (House goal 1,000,000)
            newly_achieved = (goal_accum[:, m] >= goal_target) & (goal_achieved_month == 999)
            goal_achieved_month[newly_achieved] = m

            net_worth[:, m] = (cash[:, m] + investments[:, m]) - debt[:, m]

        # Aggregate distributions
        final_nw = net_worth[:, -1]
        final_cash = cash[:, -1]

        p10_nw = float(np.percentile(final_nw, 10))
        p50_nw = float(np.percentile(final_nw, 50))
        p90_nw = float(np.percentile(final_nw, 90))

        p10_cash = float(np.percentile(final_cash, 10))
        p50_cash = float(np.percentile(final_cash, 50))
        p90_cash = float(np.percentile(final_cash, 90))

        bankruptcy_prob = float(np.mean(np.min(cash, axis=1) <= 0.0))
        goal_success_prob = float(np.mean(goal_achieved_month <= horizon_months))
        
        achieved_indices = goal_achieved_month[goal_achieved_month <= horizon_months]
        median_completion_month = int(np.median(achieved_indices)) if len(achieved_indices) > 0 else None

        # Adequate emergency fund = cash >= 3 months expenses at end of horizon
        adequate_ef_prob = float(np.mean(final_cash >= (monthly_expenses * 3.0)))

        # Precompute percentile curve trajectories across the timeline for frontend rendering
        p10_nw_curve = [float(np.percentile(net_worth[:, step], 10)) for step in range(horizon_months + 1)]
        p50_nw_curve = [float(np.percentile(net_worth[:, step], 50)) for step in range(horizon_months + 1)]
        p90_nw_curve = [float(np.percentile(net_worth[:, step], 90)) for step in range(horizon_months + 1)]

        p10_cash_curve = [float(np.percentile(cash[:, step], 10)) for step in range(horizon_months + 1)]
        p50_cash_curve = [float(np.percentile(cash[:, step], 50)) for step in range(horizon_months + 1)]
        p90_cash_curve = [float(np.percentile(cash[:, step], 90)) for step in range(horizon_months + 1)]

        # Extract 5 sample trajectories for visualization
        sample_indices = np.linspace(0, num_simulations - 1, 5, dtype=int)
        sample_nw_trajectories = [[round(float(v), 2) for v in net_worth[idx]] for idx in sample_indices]
        sample_cash_trajectories = [[round(float(v), 2) for v in cash[idx]] for idx in sample_indices]

        return SimulationResult(
            regime=regime.value,
            num_simulations=num_simulations,
            horizon_months=horizon_months,
            median_final_net_worth=round(p50_nw, 2),
            p10_net_worth=round(p10_nw, 2),
            p90_net_worth=round(p90_nw, 2),
            median_cash_balance=round(p50_cash, 2),
            p10_cash_balance=round(p10_cash, 2),
            p90_cash_balance=round(p90_cash, 2),
            bankruptcy_exhaustion_probability=round(bankruptcy_prob, 4),
            goal_achievement_probability=round(goal_success_prob, 4),
            median_goal_completion_month=median_completion_month,
            emergency_fund_adequacy_rate=round(adequate_ef_prob, 4),
            net_worth_trajectories=sample_nw_trajectories,
            cash_trajectories=sample_cash_trajectories,
            percentile_curve_net_worth={"p10": p10_nw_curve, "p50": p50_nw_curve, "p90": p90_nw_curve},
            percentile_curve_cash={"p10": p10_cash_curve, "p50": p50_cash_curve, "p90": p90_cash_curve}
        )
