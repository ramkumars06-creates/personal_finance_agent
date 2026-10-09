"""
Frontend API Client: Encapsulates REST API calls to the FastAPI backend using httpx.
Never touches the database directly.
"""
from typing import Dict, Any, List, Optional
import httpx


class FinanceAPIClient:
    """HTTP Client wrapper for Personal Finance Agent Backend API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def set_token(self, token: Optional[str]):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # Auth Methods
    def signup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/auth/signup", json=data, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/auth/login", json={"email": email, "password": password}, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def get_profile(self) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/auth/me", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.put(f"{self.base_url}/auth/me", json=data, headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    # Ingestion & Trace Methods
    def upload_statement(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, "text/csv")}
        resp = httpx.post(f"{self.base_url}/ingestion/upload", files=files, headers=self._headers(), timeout=60.0)
        resp.raise_for_status()
        return resp.json()

    def get_agent_trace(self, execution_id: str) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/orchestrator/trace/{execution_id}", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    # Transactions Methods
    def get_transactions(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        resp = httpx.get(f"{self.base_url}/transactions", params=params, headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def update_transaction_category(self, txn_id: str, new_category: str) -> Dict[str, Any]:
        resp = httpx.put(
            f"{self.base_url}/transactions/{txn_id}/category",
            json={"new_category": new_category, "apply_to_future": True},
            headers=self._headers(),
            timeout=10.0
        )
        resp.raise_for_status()
        return resp.json()

    # Alerts Methods
    def get_alerts(self) -> List[Dict[str, Any]]:
        resp = httpx.get(f"{self.base_url}/alerts", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def submit_alert_feedback(self, alert_id: str, feedback: str) -> Dict[str, Any]:
        resp = httpx.post(
            f"{self.base_url}/alerts/{alert_id}/feedback",
            json={"feedback": feedback},
            headers=self._headers(),
            timeout=10.0
        )
        resp.raise_for_status()
        return resp.json()

    # Budgets Methods
    def get_budgets(self) -> List[Dict[str, Any]]:
        resp = httpx.get(f"{self.base_url}/budgets", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def update_budgets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        resp = httpx.put(f"{self.base_url}/budgets", json=targets, headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    # Advisor Methods
    def get_weekly_advice(self) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/advisor/weekly", headers=self._headers(), timeout=15.0)
        resp.raise_for_status()
        return resp.json()

    def accept_weekly_recommendations(self, summary_id: str) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/advisor/weekly/{summary_id}/accept", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    # Privacy & Consent Methods
    def get_consent(self) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/privacy/consent", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def update_consent(self, storage: bool, llm: bool) -> Dict[str, Any]:
        resp = httpx.post(
            f"{self.base_url}/privacy/consent",
            json={"transaction_storage_consent": storage, "llm_processing_consent": llm},
            headers=self._headers(),
            timeout=10.0
        )
        resp.raise_for_status()
        return resp.json()

    def export_data(self) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/privacy/export", headers=self._headers(), timeout=15.0)
        resp.raise_for_status()
        return resp.json()

    def delete_account(self) -> Dict[str, Any]:
        resp = httpx.delete(f"{self.base_url}/privacy/account", headers=self._headers(), timeout=15.0)
        resp.raise_for_status()
        return resp.json()

    # Demo Mode
    def seed_demo(self) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/demo/seed", timeout=15.0)
        resp.raise_for_status()
        return resp.json()
