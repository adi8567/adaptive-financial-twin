# ADAPTIVE FINANCIAL TWIN (AFT)
> **A Living, Stateful Digital Twin of Your Financial Life**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-green)
![Next.js](https://img.shields.io/badge/Next.js-14.2-black)
![Tests](https://img.shields.io/badge/tests-8%2F8%20passed-brightgreen)

---

## 1. Executive Summary & Paradigm Shift
Traditional personal finance tools suffer from fundamental flaws:
1. **Expense Trackers**: Merely backward-looking static charts.
2. **Generic Chatbots**: Unconstrained text engines prone to numerical hallucinations and arbitrary financial advice.
3. **Static Robo-Advisors**: Fixed rule engines that fail to model cognitive bias, labor market disruptions, or life transitions.

**Adaptive Financial Twin** fundamentally redefines financial technology by introducing an **event-sourced, stateful living model** of an individual’s financial reality. The system couples deterministic state transitions with high-dimension stochastic Monte Carlo multi-regime forecasts, empirical behavioral economics friction metrics, and constrained reinforcement learning.

---

## 2. Core Closed-Loop System Architecture

```
 REAL FINANCIAL DATA (Bank, CC, EMI, Investments)
         ↓
 FINANCIAL TWIN STATE ENGINE (Deterministic Event-Sourced Transition)
         ↓
 BEHAVIORAL ECONOMICS ENGINE (Present Bias, Loss Aversion, Discipline)
         ↓
 STOCHASTIC SIMULATION (10,000 Monte Carlo Paths across 8 Regimes)
         ↓
 REINFORCEMENT LEARNING POLICY (Gymnasium Decision Optimizer)
         ↓
 FINANCIAL SAFETY & BEHAVIORAL CONSTRAINTS LAYER
         ↓
 ADAPTIVE RECOMMENDATION ENGINE (Ranked, Audited, Traceable)
         ↓
 USER INTERACTION / COPILOT (Grounded in Verified Twin State & RAG)
         ↓
 NEW TRANSACTION / LIFE EVENT
         ↓
 TWIN UPDATES (Continuous Cycle)
```

---

## 3. The 12 Subsystem Modules

| Subsystem | Location | Technologies | Core Responsibility |
|---|---|---|---|
| **Financial Foundation** | `backend/app/models` | SQLAlchemy, SQLite/PostgreSQL | Users, Accounts, Transactions, Assets, Liabilities, Goals. |
| **Financial Twin** | `backend/app/services` | Event-Sourcing Pipeline | $\text{State}(t+1) = \text{Transition}(\text{State}(t), \text{Event})$. Replayable, immutable. |
| **Simulation Engine** | `simulation/` | NumPy Vectorization, SciPy | 10,000 Monte Carlo paths over 8 macroeconomic regimes. |
| **Behavioral Engine** | `behavioral_engine/` | Rule & Feature Extractor | Extracts Present Bias ($\beta$), Loss Aversion ($\lambda$), and applies hard guardrails. |
| **RL Decision Engine** | `rl/` | Gymnasium, Stable-Baselines3 | 8-action simulated financial environment with multi-objective reward. |
| **Safety Engine** | `recommendation_engine/` | Invariant Validator | Prevents liquidity starvation, excessive leverage, or dangerous allocations. |
| **Adaptive Recommender** | `recommendation_engine/` | Ranking & Auditing Pipeline | Generates explanations with deterministic root reasons & simulation evidence. |
| **RAG Knowledge Base** | `rag/` | Semantic Retrieval, Citations | FPSB liquidity standards, debt avalanche rules, Thaler behavioral nudges. |
| **AI Copilot** | `llm/` | Grounded Synthesis Layer | Answering life questions (e.g. Car Affordability) without number hallucination. |
| **What-If Time Machine** | `backend/app/api/v1` | Multi-Plan Comparator | Side-by-side stochastic comparison of Plan A vs Plan B. |
| **Bloomberg-Style UI** | `frontend/` | Next.js 14, React 18, Tailwind | Real-time terminal with health metrics, regime pickers, and charts. |
| **Security & Privacy** | `backend/app/core` | JWT, Salted Hashes, PII Masks | Data export, right-to-be-forgotten, masked account numbers. |

---

## 4. Canonical Persona: Alex (DEMO MODE)
- **Age**: 27
- **Monthly Income**: ₹100,000 (Software Engineer)
- **Monthly Expenses**: ₹62,000 (Rent: ₹28,000, EMI: ₹14,000, Essentials: ₹20,000)
- **Emergency Reserve**: ₹250,000 (Liquid Bank Account)
- **Investments**: ₹500,000 (Large Cap Mutual Funds & Equities)
- **Liabilities**: ₹300,000 (Auto Loan at 9.5% APR)
- **Primary Goal**: ₹1,000,000 House Down Payment (36 months)
- **Behavioral Profile**: Present Bias: High (0.76), Loss Aversion: Medium (0.58), Discipline: Medium (0.68).

---

## 5. Quickstart & Verification

### Running the API & Engines:
```powershell
# Navigate to project root
cd C:\Users\ADITYA\.gemini\antigravity\scratch\adaptive-financial-twin

# Run backend API
python -m uvicorn backend.main:app --port 8000 --reload
```

### Running Automated Test Suite:
```powershell
python -m pytest tests/test_system.py -v
```

### Running RL Policy Benchmark:
```powershell
python -m rl.training.evaluate_agent
```

---

## 6. Disclaimers & Regulatory Boundary
Adaptive Financial Twin is an algorithmic research and decision-support modeling platform. Simulations are stochastic scenario estimates based on historical volatility parameters and do not guarantee future returns or fiduciary outcomes.
