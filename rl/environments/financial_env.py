import numpy as np
from typing import Dict, Any, Tuple, Optional
import enum

class FinancialAction(int, enum.Enum):
    INCREASE_SAVINGS = 0
    DECREASE_DISCRETIONARY = 1
    INCREASE_INVESTMENT = 2
    DECREASE_INVESTMENT = 3
    PAY_DEBT = 4
    BUILD_EMERGENCY_FUND = 5
    DELAY_GOAL = 6
    CONTINUE_CURRENT_PLAN = 7

ACTION_NAMES = [
    "increase_savings",
    "decrease_discretionary_spending",
    "increase_investment",
    "decrease_investment",
    "pay_debt",
    "build_emergency_fund",
    "delay_goal",
    "continue_current_plan"
]

class FinancialTwinEnv:
    """
    Simulated Financial Environment adhering to standard Gymnasium state/step specifications.
    
    STATE VECTOR (11 elements, normalized):
    0: cash (relative to 1,000,000 scale)
    1: income (relative to 200,000)
    2: expenses (relative to 200,000)
    3: debt (relative to 1,000,000)
    4: investment (relative to 2,000,000)
    5: emergency_fund_months (relative to 12)
    6: goal_progress (0 to 1)
    7: risk_tolerance (0: low, 0.5: med, 1.0: high)
    8: behavioral_present_bias (0 to 1)
    9: financial_stress (0 to 1)
    10: market_regime (0: normal, 0.33: bear, 0.66: bull, 1.0: recession)

    ACTIONS:
    8 discrete financial allocation interventions.
    """

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self.action_space_n = 8
        self.observation_dim = 11
        self.max_steps = 36 # 36 months horizon
        self.current_step = 0
        self.initial_config = initial_state or {
            "cash": 150000.0,
            "income": 100000.0,
            "expenses": 62000.0,
            "debt": 300000.0,
            "investment": 500000.0,
            "goal_target": 1000000.0,
            "goal_current": 250000.0,
            "risk_tolerance": "medium",
            "present_bias": 0.76
        }
        self.reset()

    def reset(self) -> np.ndarray:
        self.current_step = 0
        self.cash = float(self.initial_config["cash"])
        self.income = float(self.initial_config["income"])
        self.expenses = float(self.initial_config["expenses"])
        self.debt = float(self.initial_config["debt"])
        self.investment = float(self.initial_config["investment"])
        self.goal_target = float(self.initial_config.get("goal_target", 1000000.0))
        self.goal_current = float(self.initial_config.get("goal_current", 250000.0))
        self.risk_tol = self.initial_config.get("risk_tolerance", "medium")
        self.present_bias = float(self.initial_config.get("present_bias", 0.76))
        self.market_regime = 0.0 # Normal
        return self._get_obs()

    def _get_obs(self) -> np.ndarray:
        ef_months = self.cash / self.expenses if self.expenses > 0 else 0.0
        goal_prog = self.goal_current / self.goal_target if self.goal_target > 0 else 0.0
        stress = min(1.0, max(0.0, (1.0 - (ef_months / 6.0)) * 0.5 + (self.debt / (self.income * 6.0)) * 0.5))
        risk_num = 0.5 if self.risk_tol == "medium" else (1.0 if self.risk_tol == "high" else 0.0)

        obs = np.array([
            min(2.0, self.cash / 1000000.0),
            min(2.0, self.income / 200000.0),
            min(2.0, self.expenses / 200000.0),
            min(2.0, self.debt / 1000000.0),
            min(2.0, self.investment / 2000000.0),
            min(2.0, ef_months / 12.0),
            min(1.0, goal_prog),
            risk_num,
            self.present_bias,
            stress,
            self.market_regime
        ], dtype=np.float32)
        return obs

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.current_step += 1
        act = FinancialAction(action)
        prev_net_worth = (self.cash + self.investment) - self.debt

        penalty = 0.0
        constraint_violated = False

        # Action Execution Dynamics
        if act == FinancialAction.INCREASE_SAVINGS:
            # Shift 5,000 from expenses to cash savings
            self.expenses = max(30000.0, self.expenses - 5000.0)
            self.cash += 5000.0
        elif act == FinancialAction.DECREASE_DISCRETIONARY:
            # Cut 4,000 discretionary spend
            self.expenses = max(30000.0, self.expenses - 4000.0)
            self.cash += 4000.0
        elif act == FinancialAction.INCREASE_INVESTMENT:
            # If emergency fund is inadequate, apply severe constraint penalty
            if (self.cash / self.expenses) < 2.5:
                penalty += 15.0 # Constraint violation: investing before safe runway
                constraint_violated = True
            transfer = min(10000.0, max(0.0, self.cash - 50000.0))
            self.cash -= transfer
            self.investment += transfer
        elif act == FinancialAction.DECREASE_INVESTMENT:
            # Liquidate 15,000 to cash
            transfer = min(15000.0, self.investment)
            self.investment -= transfer
            self.cash += transfer
        elif act == FinancialAction.PAY_DEBT:
            # Prepay 10,000 towards debt
            transfer = min(10000.0, self.debt, max(0.0, self.cash - 30000.0))
            self.cash -= transfer
            self.debt -= transfer
        elif act == FinancialAction.BUILD_EMERGENCY_FUND:
            # Prioritize liquid reserve accumulation
            transfer = min(8000.0, max(0.0, self.income - self.expenses))
            self.cash += transfer
            self.goal_current += transfer * 0.2
        elif act == FinancialAction.DELAY_GOAL:
            # Reduces pressure on monthly contributions
            pass
        elif act == FinancialAction.CONTINUE_CURRENT_PLAN:
            pass

        # Monthly Passive Evolution
        # Investment return (approx 0.8% monthly = ~10% annual)
        self.investment *= 1.008
        # Debt interest (0.75% monthly)
        if self.debt > 0:
            self.debt = max(0.0, self.debt * 1.0075 - 14000.0) # monthly EMI
            self.cash -= 14000.0

        cur_net_worth = (self.cash + self.investment) - self.debt
        delta_nw = cur_net_worth - prev_net_worth

        # REWARD FUNCTION FORMULATION:
        # Combines net worth growth, emergency resilience, goal progress, debt reduction, and stress minimization
        ef_months = self.cash / self.expenses if self.expenses > 0 else 0.0
        goal_ratio = self.goal_current / self.goal_target if self.goal_target > 0 else 0.0
        
        r_nw = (delta_nw / 10000.0) * 1.5
        r_resilience = 3.0 if ef_months >= 3.0 else (ef_months - 3.0) * 4.0
        r_goal = goal_ratio * 5.0
        r_debt = - (self.debt / 100000.0) * 1.0
        r_stress = - ((1.0 - (ef_months / 6.0)) if ef_months < 6.0 else 0.0) * 2.0

        # High cash exhaustion penalty
        if self.cash <= 0.0:
            penalty += 50.0

        reward = r_nw + r_resilience + r_goal + r_debt + r_stress - penalty

        done = (self.current_step >= self.max_steps) or (self.cash < -50000.0)
        truncated = False
        info = {
            "net_worth": cur_net_worth,
            "cash": self.cash,
            "debt": self.debt,
            "emergency_fund_months": ef_months,
            "goal_ratio": goal_ratio,
            "constraint_violated": constraint_violated,
            "action_taken": ACTION_NAMES[action]
        }
        return self._get_obs(), float(reward), done, truncated, info
