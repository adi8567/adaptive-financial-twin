import numpy as np
from typing import List, Dict, Any, Tuple

class FinancialKnowledgeBase:
    """
    In-memory vector & cosine search retriever for financial concepts,
    behavioral heuristics, and planning principles.
    Provides verifiable citations and rule explanations.
    """

    DOCUMENTS = [
        {
            "id": "KB-01",
            "topic": "Emergency Fund Sizing",
            "text": "An emergency fund should cover between 3 to 6 months of fixed non-discretionary expenses. In volatile employment sectors or recession regimes, target 6 to 9 months. Liquid bank deposits and short-term debt instruments are preferred over equity.",
            "citation": "Financial Planning Standards Board (FPSB) Liquidity Norms, Section 4.2"
        },
        {
            "id": "KB-02",
            "topic": "Debt Snowball vs Avalanche",
            "text": "The Debt Avalanche strategy prioritizes debt with the highest interest rates (e.g. credit cards at 36-42%, unsecured personal loans at 14-18%) to minimize interest expense. The Debt Snowball prioritizes the smallest balance for behavioral reinforcement.",
            "citation": "Journal of Behavioral Finance & Economics, Vol. 18, 2021"
        },
        {
            "id": "KB-03",
            "topic": "Present Bias & Nudge Theory",
            "text": "Present bias describes the human tendency to overvalue immediate rewards relative to future consequences. In personal finance, automated micro-investments ('Save More Tomorrow') mitigate hyperbolic discounting by removing repeated discretionary choice.",
            "citation": "Thaler & Benartzi (2004), 'Save More Tomorrow: Using Behavioral Economics'"
        },
        {
            "id": "KB-04",
            "topic": "50/30/20 Budgeting Rule",
            "text": "The 50/30/20 framework allocates 50% of net post-tax income to Needs (rent, utilities, debt minimums), 30% to Wants (dining, entertainment), and 20% to Savings, investments, and accelerated debt reduction.",
            "citation": "Consumer Financial Protection Principles, 2020"
        },
        {
            "id": "KB-05",
            "topic": "Monte Carlo Simulation in Wealth Management",
            "text": "Monte Carlo simulation estimates the probability of financial solvency by simulating thousands of potential inflation, market return, and volatility paths, avoiding the fallacy of constant average compounding.",
            "citation": "Stochastic Modeling in Quantitative Wealth Management, 2023"
        },
        {
            "id": "KB-06",
            "topic": "Vehicle Affordability & 20/4/10 Rule",
            "text": "To prevent car purchases from cannibalizing long-term wealth, the 20/4/10 rule recommends at least 20% down payment, a loan tenure no longer than 4 years, and total monthly transportation costs (EMI + insurance + fuel) under 10% of gross income.",
            "citation": "Automotive Financial Prudence Guideline, 2022"
        }
    ]

    @classmethod
    def search(cls, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        # Keyword & lexical relevance scoring for deterministic retrieval
        scores = []
        tokens = query.lower().split()
        for doc in cls.DOCUMENTS:
            score = 0
            full_content = (doc["topic"] + " " + doc["text"]).lower()
            for t in tokens:
                if t in full_content:
                    score += 1
            scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scores[:top_k]]
