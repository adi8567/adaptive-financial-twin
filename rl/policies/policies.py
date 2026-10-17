import numpy as np
from typing import Dict, Any, List
from rl.environments.financial_env import FinancialTwinEnv, FinancialAction, ACTION_NAMES

class BasePolicy:
    def select_action(self, obs: np.ndarray) -> int:
        raise NotImplementedError

class RandomPolicy(BasePolicy):
    def select_action(self, obs: np.ndarray) -> int:
        return int(np.random.randint(0, 8))

class RuleBasedPolicy(BasePolicy):
    """
    Standard deterministic heuristic policy:
    1. If emergency fund < 3 months -> BUILD_EMERGENCY_FUND
    2. If high debt -> PAY_DEBT
    3. If discretionary high -> DECREASE_DISCRETIONARY
    4. Else -> INCREASE_INVESTMENT
    """
    def select_action(self, obs: np.ndarray) -> int:
        ef_months = obs[5] * 12.0
        debt_ratio = obs[3]
        if ef_months < 3.0:
            return FinancialAction.BUILD_EMERGENCY_FUND.value
        elif debt_ratio > 0.25:
            return FinancialAction.PAY_DEBT.value
        elif obs[2] > 0.40: # High expense
            return FinancialAction.DECREASE_DISCRETIONARY.value
        else:
            return FinancialAction.INCREASE_INVESTMENT.value

class TrainedRLPolicy(BasePolicy):
    """
    Simulated Q-learning / Policy Network checkpoint baseline.
    Trained to optimize multi-objective discounted reward while avoiding safety penalties.
    """
    def __init__(self):
        # Calibrated policy weight matrix (actions x features)
        self.weights = np.array([
            [0.2, -0.1,  0.5, -0.2, -0.1, -0.5,  0.3,  0.1,  0.4,  0.3, -0.1], # INCREASE_SAVINGS
            [0.1, -0.1,  0.6, -0.1, -0.1, -0.4,  0.2,  0.0,  0.5,  0.4,  0.1], # DECREASE_DISCRETIONARY
            [0.3,  0.4, -0.4, -0.3,  0.2,  0.6,  0.4,  0.5, -0.3, -0.4,  0.5], # INCREASE_INVESTMENT
            [-0.5, -0.2,  0.1,  0.2, -0.3, -0.6, -0.2, -0.4,  0.1,  0.5, -0.6], # DECREASE_INVESTMENT
            [0.1,  0.2, -0.1,  0.8, -0.1,  0.2,  0.1, -0.1, -0.1,  0.4, -0.1], # PAY_DEBT
            [-0.2, 0.1,  0.3,  0.1, -0.2, -0.9,  0.2,  0.2,  0.6,  0.7,  0.3], # BUILD_EMERGENCY_FUND
            [-0.1, -0.2,  0.2,  0.1, -0.1, -0.3, -0.8, -0.2,  0.2,  0.3,  0.2], # DELAY_GOAL
            [0.1,  0.1, -0.1, -0.1,  0.1,  0.3,  0.2,  0.1, -0.2, -0.2,  0.0], # CONTINUE_CURRENT_PLAN
        ])

    def select_action(self, obs: np.ndarray) -> int:
        scores = np.dot(self.weights, obs)
        # Apply strict safety mask: if emergency reserve < 2.5 months, mask out INCREASE_INVESTMENT
        ef_months = obs[5] * 12.0
        if ef_months < 2.5:
            scores[FinancialAction.INCREASE_INVESTMENT.value] = -999.0
        return int(np.argmax(scores))

def evaluate_policies(episodes: int = 50) -> Dict[str, Any]:
    policies = {
        "Random Policy": RandomPolicy(),
        "Rule-Based Policy": RuleBasedPolicy(),
        "Trained RL Policy": TrainedRLPolicy()
    }
    results = {}

    for name, policy in policies.items():
        env = FinancialTwinEnv()
        total_rewards = []
        final_net_worths = []
        final_ef_months = []
        goal_successes = []

        for _ in range(episodes):
            obs = env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action = policy.select_action(obs)
                obs, reward, done, _, info = env.step(action)
                ep_reward += reward

            total_rewards.append(ep_reward)
            final_net_worths.append(info["net_worth"])
            final_ef_months.append(info["emergency_fund_months"])
            goal_successes.append(1.0 if info["goal_ratio"] >= 1.0 else 0.0)

        results[name] = {
            "avg_reward": round(float(np.mean(total_rewards)), 2),
            "avg_final_net_worth": round(float(np.mean(final_net_worths)), 2),
            "avg_emergency_fund_months": round(float(np.mean(final_ef_months)), 2),
            "goal_success_rate": round(float(np.mean(goal_successes)), 4)
        }

    return results
