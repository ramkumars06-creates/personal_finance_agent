"""
3. Anomaly Agent: Deterministic, explainable anomaly detection with multi-signal thresholding and cold-start fallback.
"""
from typing import Any

import numpy as np


class AnomalyAgent:
    """Agent that analyzes spending patterns to highlight explainable anomalies."""

    def detect_anomalies(
        self,
        new_transactions: list[dict[str, Any]],
        historical_transactions: list[dict[str, Any]],
        user_feedback_history: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """
        Evaluate new transactions against user historical baselines.
        """
        anomalies = []
        is_cold_start = len(historical_transactions) < 5
        
        # Build category baselines from historical data
        cat_history: dict[str, list[float]] = {}
        known_merchants = set()

        for h in historical_transactions:
            cat = h.get("category", "other")
            amt = float(h.get("amount", 0.0))
            m = h.get("normalized_merchant", "").lower()
            
            cat_history.setdefault(cat, []).append(amt)
            if m:
                known_merchants.add(m)

        for txn in new_transactions:
            signals = []
            reasons = []
            severity = "low"

            amt = float(txn.get("amount", 0.0))
            cat = txn.get("category", "other")
            merchant = txn.get("normalized_merchant", "").lower()
            txn_type = txn.get("transaction_type", "debit")

            # Only analyze debit spending
            if txn_type != "debit":
                continue

            # Signal 1: Category Baseline Deviation (Z-score / IQR)
            history_amts = cat_history.get(cat, [])
            if len(history_amts) >= 2:
                mean = float(np.mean(history_amts))
                std = float(np.std(history_amts))
                q25, q75 = np.percentile(history_amts, [25, 75])
                iqr = q75 - q25

                z_score = (amt - mean) / std if std > 0 else 0.0
                upper_bound = q75 + 1.5 * iqr

                if z_score > 2.5 or (iqr > 0 and amt > upper_bound):
                    signals.append("category_baseline_deviation")
                    reasons.append(f"Amount Rs. {amt:,.2f} is significantly higher than your typical {cat} average (Rs. {mean:,.2f}).")
                    if z_score > 3.5:
                        severity = "high"
                    else:
                        severity = "medium"
            elif is_cold_start:
                # Cold start fallback threshold
                if amt > 3000.0:
                    signals.append("cold_start_large_amount")
                    reasons.append(f"Amount Rs. {amt:,.2f} is high for a new user baseline (Baseline still learning).")
                    severity = "medium"

            # Signal 2: Unseen Merchant
            if historical_transactions and merchant and (merchant not in known_merchants):
                signals.append("unseen_merchant")
                reasons.append(f"First time transaction detected with merchant '{txn.get('normalized_merchant')}'.")
                if amt > 2000.0:
                    severity = "medium"

            # Signal 3: Large Transaction Threshold
            if amt >= 5000.0:
                signals.append("high_single_transaction_value")
                reasons.append(f"Transaction of Rs. {amt:,.2f} exceeds standard single-purchase benchmark.")

            # Decision Logic: Requires >= 2 signals OR 1 high severity signal
            if len(signals) >= 2 or severity == "high":
                alert = {
                    "transaction_id": txn.get("id", ""),
                    "merchant": txn.get("normalized_merchant", "Unknown"),
                    "amount": amt,
                    "alert_type": signals[0] if signals else "unusual_spending",
                    "severity": severity,
                    "plain_language_reason": " ".join(reasons),
                    "signals_fired": signals,
                    "user_feedback": "pending"
                }
                anomalies.append(alert)

        return anomalies
