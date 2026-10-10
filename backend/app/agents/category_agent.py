"""
2. Category Agent: Hybrid classification via User Rules -> Keyword Engine -> LLM Gateway.
"""
from typing import Any

from app.llm.gateway import LLMGateway
from app.repositories.user_scoped_repo import CategoryRuleRepository
from sqlalchemy.orm import Session


class CategoryAgent:
    """Agent that classifies transactions into standard categories."""

    VALID_CATEGORIES = [
        "food", "groceries", "transport", "bills",
        "rent", "shopping", "entertainment", "health",
        "education", "other"
    ]

    def __init__(self, llm_gateway: LLMGateway | None = None):
        self.llm = llm_gateway or LLMGateway()

    def categorize_transactions(
        self,
        transactions: list[dict[str, Any]],
        db_session: Session | None = None,
        user_id: str | None = None
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """
        Categorize a batch of normalized transactions.
        """
        user_rule_repo = None
        if db_session and user_id:
            user_rule_repo = CategoryRuleRepository(db_session, user_id)

        stats = {"user_rule": 0, "rule": 0, "llm": 0, "fallback": 0}
        categorized = []

        for txn in transactions:
            merchant = txn.get("normalized_merchant", "")
            
            # Step 1: Per-user rules check
            matched_user_rule = None
            if user_rule_repo:
                matched_user_rule = user_rule_repo.find_matching_rule(merchant)

            if matched_user_rule:
                cat = matched_user_rule.target_category
                conf = 1.0
                method = "user_rule"
                stats["user_rule"] += 1
            else:
                # Step 2: Global Rule / LLM Gateway check
                res = self.llm.categorize_merchant(merchant)
                cat = res.get("category", "other")
                conf = res.get("confidence", 0.5)
                method = res.get("method", "rule")
                
                if method == "rule":
                    stats["rule"] += 1
                elif method == "llm":
                    stats["llm"] += 1
                else:
                    stats["fallback"] += 1

            # Ensure valid category
            if cat not in self.VALID_CATEGORIES:
                cat = "other"

            txn_copy = txn.copy()
            txn_copy["category"] = cat
            txn_copy["category_confidence"] = float(conf)
            txn_copy["categorization_method"] = method
            categorized.append(txn_copy)

        return categorized, stats
