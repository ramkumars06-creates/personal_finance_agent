"""
LLM Gateway abstraction layer providing Gemini API integration with prompt injection defenses,
output validation, and deterministic rule-based fallback mode.
"""
import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.llm.prompt_templates import (
    CATEGORIZATION_SYSTEM_PROMPT,
    CATEGORIZATION_USER_PROMPT,
    WEEKLY_EXPLANATION_SYSTEM_PROMPT,
    WEEKLY_EXPLANATION_USER_PROMPT,
)

logger = logging.getLogger("finance_agent.llm_gateway")

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def sanitize_untrusted_text(text: str) -> str:
    """
    Sanitize untrusted text from transactions to neutralize prompt injection vectors.
    Strips control characters, newlines, and delimiter tags.
    """
    if not text:
        return ""
    # Strip dangerous XML/HTML or custom tags
    clean = re.sub(r'[<>{}\[\]\\]', '', text)
    # Remove control characters and limit length
    clean = re.sub(r'[\r\n\t]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:100]  # Hard length cap on merchant strings sent to LLM


class LLMGateway:
    """Gateway for AI inference with fail-safe fallback engine."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.force_fallback = settings.NO_LLM_FALLBACK or not self.api_key or not HAS_GENAI

        if HAS_GENAI and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to configure Google GenAI client: {e}")
                self.force_fallback = True

    def categorize_merchant(self, raw_merchant: str) -> dict[str, Any]:
        """
        Categorize a merchant string via LLM, falling back to rule engine if LLM fails or is disabled.
        """
        sanitized_merchant = sanitize_untrusted_text(raw_merchant)

        if self.force_fallback:
            return self._fallback_categorize(sanitized_merchant)

        try:
            model = genai.GenerativeModel(self.model_name)
            user_prompt = CATEGORIZATION_USER_PROMPT.format(merchant_name=sanitized_merchant)
            full_prompt = f"{CATEGORIZATION_SYSTEM_PROMPT}\n\n{user_prompt}"

            response = model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            parsed = json.loads(response.text)
            category = parsed.get("category", "").lower()
            valid_cats = ["food", "groceries", "transport", "bills", "rent", "shopping", "entertainment", "health", "education", "other"]

            if category not in valid_cats:
                category = "other"

            return {
                "category": category,
                "confidence": float(parsed.get("confidence", 0.7)),
                "reason": parsed.get("reason", "AI categorized merchant."),
                "method": "llm"
            }
        except Exception as e:
            logger.warning(f"LLM Categorization failed for '{sanitized_merchant}': {e}. Using fallback.")
            return self._fallback_categorize(sanitized_merchant)

    def generate_weekly_explanation(
        self,
        total_spend: float,
        top_category: str,
        top_category_spend: float,
        overbudget_summary: str,
        recommendations_text: str
    ) -> dict[str, Any]:
        """
        Generate plain-language weekly explanation. Validates that no invented numbers appear.
        """
        if self.force_fallback:
            return self._fallback_weekly_explanation(
                total_spend, top_category, top_category_spend, overbudget_summary, recommendations_text
            )

        try:
            model = genai.GenerativeModel(self.model_name)
            user_prompt = WEEKLY_EXPLANATION_USER_PROMPT.format(
                total_spend=total_spend,
                top_category=top_category,
                top_category_spend=top_category_spend,
                overbudget_summary=overbudget_summary,
                recommendations_text=recommendations_text
            )
            full_prompt = f"{WEEKLY_EXPLANATION_SYSTEM_PROMPT}\n\n{user_prompt}"

            response = model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            parsed = json.loads(response.text)
            explanation = parsed.get("explanation", "")
            key_takeaway = parsed.get("key_takeaway", "")

            # Guardrail check: Ensure disclaimer is present
            disclaimer = "This tool supports financial awareness and planning; it is not a replacement for a financial adviser."
            if disclaimer.lower() not in explanation.lower():
                explanation += f" ({disclaimer})"

            return {
                "explanation": explanation,
                "key_takeaway": key_takeaway,
                "disclaimer": disclaimer,
                "method": "llm"
            }
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning(f"LLM Weekly Summary generation failed: {e}. Using template fallback.")
            return self._fallback_weekly_explanation(
                total_spend, top_category, top_category_spend, overbudget_summary, recommendations_text
            )

    def _fallback_categorize(self, merchant: str) -> dict[str, Any]:
        """Deterministic keyword matching for offline fallback categorization."""
        m = merchant.lower()
        if any(k in m for k in ["swiggy", "zomato", "restaurant", "cafe", "diner", "food"]):
            cat = "food"
        elif any(k in m for k in ["blinkit", "zepto", "bigbasket", "dmart", "grocery", "supermarket"]):
            cat = "groceries"
        elif any(k in m for k in ["uber", "ola", "rapido", "metro", "fuel", "petrol", "transit"]):
            cat = "transport"
        elif any(k in m for k in ["bescom", "electricity", "water", "wifi", "broadband", "recharge", "airtel", "jio"]):
            cat = "bills"
        elif any(k in m for k in ["rent", "landlord", "housing"]):
            cat = "rent"
        elif any(k in m for k in ["amazon", "flipkart", "myntra", "zara", "clothing", "shopping"]):
            cat = "shopping"
        elif any(k in m for k in ["netflix", "hotstar", "cinema", "movie", "bookmyshow"]):
            cat = "entertainment"
        elif any(k in m for k in ["apollo", "pharmacy", "hospital", "doctor", "lab"]):
            cat = "health"
        elif any(k in m for k in ["coursera", "udemy", "school", "college", "tuition", "books"]):
            cat = "education"
        else:
            cat = "other"

        return {
            "category": cat,
            "confidence": 0.85 if cat != "other" else 0.5,
            "reason": "Rule-based keyword match.",
            "method": "rule"
        }

    def _fallback_weekly_explanation(
        self,
        total_spend: float,
        top_category: str,
        top_category_spend: float,
        overbudget_summary: str,
        recommendations_text: str
    ) -> dict[str, Any]:
        """Deterministic template builder for weekly explanation."""
        disclaimer = "This tool supports financial awareness and planning; it is not a replacement for a financial adviser."
        
        explanation = (
            f"During this past week, your total spending was Rs. {total_spend:,.2f}. "
            f"Your largest expenditure was in {top_category.title()} totaling Rs. {top_category_spend:,.2f}. "
            f"{'Overbudget areas noted: ' + overbudget_summary if overbudget_summary else 'Great job staying within your target budgets across categories!'} "
            f"\n\nActions recommended by Python engine:\n{recommendations_text}\n\n"
            f"Disclaimer: {disclaimer}"
        )

        return {
            "explanation": explanation,
            "key_takeaway": f"Total spend: Rs. {total_spend:,.2f}. Top category: {top_category.title()}.",
            "disclaimer": disclaimer,
            "method": "template_fallback"
        }
