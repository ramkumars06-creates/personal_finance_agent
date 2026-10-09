"""
5. Weekly Advisor Agent: Python-calculated budget recommendations coupled with LLM explanation rephrasing.
"""
from typing import Dict, Any, List, Optional
from app.llm.gateway import LLMGateway


class AdvisorAgent:
    """Agent generating actionable recommendations and weekly financial awareness summaries."""

    DISCLAIMER = "This tool supports financial awareness and planning; it is not a replacement for a financial adviser."

    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()

    def generate_weekly_advice(
        self,
        budget_analysis: Dict[str, Any],
        savings_goal: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate recommendations (computed 100% in Python) and plain-language summary via LLM.
        """
        category_analysis = budget_analysis.get("category_analysis", {})
        total_weekly_spend = budget_analysis.get("total_weekly_spend", 0.0)
        overspend_categories = budget_analysis.get("overspend_categories", [])

        # Step 1: Compute Recommendations deterministically in Python
        recommendations = []
        
        # Identify top spending category
        sorted_categories = sorted(
            category_analysis.values(),
            key=lambda x: x["actual_amount"],
            reverse=True
        )
        
        top_cat = sorted_categories[0]["category"] if sorted_categories else "other"
        top_cat_spend = sorted_categories[0]["actual_amount"] if sorted_categories else 0.0

        # Recommendation 1: Overspend correction
        for cat in overspend_categories[:2]:
            c_info = category_analysis[cat]
            over_rs = c_info["variance_rs"]
            suggested_reduction = round(over_rs * 0.7, 2)
            
            recommendations.append({
                "category": cat.title(),
                "rs_change": -suggested_reduction,
                "reason": f"Spending in {cat.title()} exceeded your weekly target by Rs. {over_rs:,.2f}.",
                "savings_effect": f"Trimming Rs. {suggested_reduction:,.2f} brings your {cat.title()} category back toward baseline target."
            })

        # Recommendation 2: High spend optimization if no overspend
        if len(recommendations) < 2 and sorted_categories:
            highest = sorted_categories[0]
            cat_name = highest["category"]
            act_amt = highest["actual_amount"]
            if act_amt > 500:
                potential_saving = round(act_amt * 0.15, 2)
                recommendations.append({
                    "category": cat_name.title(),
                    "rs_change": -potential_saving,
                    "reason": f"{cat_name.title()} was your largest expense category this week (Rs. {act_amt:,.2f}).",
                    "savings_effect": f"A modest 15% reduction frees up Rs. {potential_saving:,.2f} toward your savings goal."
                })

        # Recommendation 3: General positive reinforcement
        target_savings_impact = sum(abs(r["rs_change"]) for r in recommendations)
        if not recommendations:
            recommendations.append({
                "category": "Overall Budget",
                "rs_change": 0.0,
                "reason": "You maintained excellent budget control across all categories this week!",
                "savings_effect": "Consistent habits like this support long-term financial stability."
            })

        # Step 2: Prepare formatted text for LLM explanation
        overbudget_summary = ", ".join(overspend_categories) if overspend_categories else "None"
        recs_text = "\n".join([
            f"- {r['category']}: Suggest changing spend by Rs. {r['rs_change']:.2f}. Reason: {r['reason']}"
            for r in recommendations
        ])

        # Step 3: Invoke LLM Gateway for safe phrasing
        llm_res = self.llm.generate_weekly_explanation(
            total_spend=total_weekly_spend,
            top_category=top_cat,
            top_category_spend=top_cat_spend,
            overbudget_summary=overbudget_summary,
            recommendations_text=recs_text
        )

        return {
            "total_weekly_spend": total_weekly_spend,
            "top_category": top_cat,
            "category_breakdown": {cat: info["actual_amount"] for cat, info in category_analysis.items()},
            "recommendations": recommendations,
            "potential_weekly_savings": round(target_savings_impact, 2),
            "llm_explanation": llm_res.get("explanation", ""),
            "disclaimer": self.DISCLAIMER,
            "generation_method": llm_res.get("method", "template_fallback")
        }
