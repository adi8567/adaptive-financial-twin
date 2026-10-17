# ARCHITECTURE: ADAPTIVE FINANCIAL TWIN

## 1. System Vision & Paradigm Shift
The **Adaptive Financial Twin** is a living, stateful, event-driven digital twin of an individual's financial ecosystem.
Unlike traditional static expense trackers, chatbots, or generic robo-advisors:
1. **Dynamic Statefulness**: Reconstructs and evolves financial states over time via deterministic event-sourcing principles.
2. **Multi-Horizon Stochastic Modeling**: Runs high-dimension Monte Carlo simulations across economic stress regimes (stagflation, recessions, market shocks, job loss) to derive empirical probability distributions rather than point predictions.
3. **Behavioral Invariance & Nudge Synthesis**: Infers empirical behavioral coefficients (present bias, loss aversion, status quo bias, discipline decay) directly from transactional signatures.
4. **Constrained Reinforcement Learning**: Simulates decision policies within a strict safety envelope; RL actions never bypass behavioral constraints or deterministic solvency limits.
5. **Decoupled Explainable AI Copilot**: LLM/RAG layers operate strictly on verified structured twin states and deterministic simulation bounds—completely preventing hallucinated balances or ungrounded financial advice.

---

## 2. High-Level System Architecture

```
                                +---------------------------+
                                |      NEXT.JS DASHBOARD    |
                                | (TypeScript + TailwindUI) |
                                +-------------+-------------+
                                              | HTTPS / WSS
                                              v
                                +---------------------------+
                                |     FASTAPI GATEWAY       |
                                | (Auth, PII Mask, Routing) |
                                +-------------+-------------+
                                              |
               +------------------------------+------------------------------+
               |                              |                              |
               v                              v                              v
    +--------------------+         +--------------------+         +--------------------+
    |   Financial Core   |         |   Financial Twin   |         |    Goal Engine     |
    | (Users, Accounts,  | <-----> |   State Machine    | <-----> | (Targets, Priority,|
    |  Txs, Balances)    |         | (Event Aggregator) |         |  Probabilities)    |
    +--------------------+         +--------------------+         +--------------------+
               |                              |                              |
               +------------------------------+------------------------------+
                                              |
                                              v
                               +-----------------------------+
                               |   Monte Carlo Simulator     |
                               | (10k+ Paths, Stress Regimes)|
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |     Behavioral Engine       |
                               |  (Bias & Friction Metrics)  |
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |    RL Decision Engine       |
                               | (Gymnasium + StableBaselines|
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |   Financial Safety Engine   |
                               | (Hard Invariants & Bounds)  |
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |    Adaptive Recommender     |
                               |  (Action Ranking & Auditing)|
                               +--------------+--------------+
                                              |
                        +---------------------+---------------------+
                        |                                           |
                        v                                           v
         +-----------------------------+             +-----------------------------+
         |     FAISS RAG Knowledge     |             |      LLM Provider Copilot   |
         |  (Citations & Core Rules)   | ----------> | (Gemini / Claude / OpenAI)  |
         +-----------------------------+             +-----------------------------+
```

---

## 3. Subsystem Decomposition & Boundaries

### 3.1 `backend/` (FastAPI + SQLAlchemy + Pydantic v2)
- **Entities**: User, Account, Transaction, Asset, Liability, Goal, FinancialSnapshot, EventLog, SimulationRun.
- **Security Boundaries**: PII tokenization, rate-limiting, strict JWT validation, sanitized error output, database tenant separation.
- **State Transition Invariant**:
  $$\text{FinancialState}(t+1) = \text{Transition}(\text{FinancialState}(t), \text{Event}_t)$$
  Calculations are 100% deterministic, auditable, and replayable from Genesis.

### 3.2 `simulation/` (NumPy + SciPy)
- Vectorized Monte Carlo engine running multi-year stochastic monthly paths ($N \ge 10,000$).
- Economic Regimes: `NORMAL`, `HIGH_INFLATION`, `RECESSION`, `BULL_MARKET`, `BEAR_MARKET`, `JOB_LOSS`, `MEDICAL_EXPENSE`, `COMBINED_STRESS`.
- Geometric Brownian Motion (GBM) with Jump Diffusion for asset valuations; regime-switching Markov shocks for labor market disruption and inflation spikes.
- Returns percentile frontiers ($P_{10}, P_{50}, P_{90}$) and bankruptcy hazard probabilities.

### 3.3 `behavioral_engine/`
- Extracts behavioral indicators from immutable ledger telemetry:
  - **Present Bias** ($\beta$): Proclivity to deplete liquid reserves pre-payday.
  - **Loss Aversion** ($\lambda$): Asymmetric portfolio rebalancing in down-markets.
  - **Goal Commitment**: Frequency and consistency of manual and scheduled goal contributions.
  - **Savings Discipline**: Variance of non-essential outflow relative to income.
- Emits explicit constraints: e.g., if $\beta > 0.70$, enforce micro-SIP automation and suppress lump-sum recommendations.

### 3.4 `rl/` (Gymnasium + Stable-Baselines3 + Rule-Based Baselines)
- Action Space: `[increase_savings, decrease_discretionary, increase_investment, decrease_investment, pay_debt, build_emergency_fund, delay_goal, continue_current_plan]`.
- Reward Formulation:
  $$R_t = w_1 \Delta \text{NetWorth}_t + w_2 \text{Resilience}_t + w_3 \text{GoalProgress}_t - w_4 \text{DebtPen}_t - w_5 \text{StressPen}_t - w_6 \text{ConstraintViolation}_t$$
- **Safety Interlock**: Actions proposed by the policy network must pass through `FinancialSafetyEngine` and `BehavioralConstraintEngine` before ranking.

### 3.5 `recommendation_engine/`
- Aggregates Twin State + Simulation Frontier + RL Candidate Actions + Behavioral Rules.
- Outputs structured recommendations with:
  - `action`: Concrete action statement.
  - `reason`: Quantitative root-cause.
  - `expected_benefit`: Quantified horizon gain (e.g., $+1.2$ months runway).
  - `behavioral_reason`: Why this matches the user's specific cognitive profile.
  - `simulation_evidence`: $P(\text{Success})$ shift from baseline to alternative.

### 3.6 `rag/` & `llm/`
- Vectorized storage (FAISS / Cosine index) storing authoritative financial frameworks, liquidity principles, and tax-efficient planning axioms.
- Strict isolation: LLM receives verified system facts as typed tool calls. LLMs are prohibited from computing arithmetic or state variables.

---

## 4. Scalability Bottlenecks & Mitigations
1. **Simulation Compute Load**:
   - *Bottleneck*: Running 10,000 Monte Carlo runs on synchronous HTTP requests will exhaust workers.
   - *Mitigation*: Vectorized NumPy array batching + asynchronous task processing (background thread pool / Celery / Redis queue) with intermediate caching of simulation matrices.
2. **State Replay Overhead**:
   - *Bottleneck*: Recomputing twin state from thousands of raw historical transactions on every query.
   - *Mitigation*: Periodic snapshotting (monthly checkpoint states) in `financial_snapshots` table + incremental replay from latest snapshot.
3. **Database Write Concurrency**:
   - *Bottleneck*: Event log ingestion contention during high-frequency transaction syncing.
   - *Mitigation*: Append-only event store with optimistic locking and read-replica splitting.
