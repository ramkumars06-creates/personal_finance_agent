"""
Repository pattern providing strict multi-tenant data isolation.
All database access methods enforce mandatory user_id filtering.
"""
from typing import Generic, TypeVar

from app.core.database import enable_postgres_rls
from app.models.db_models import CategoryRule, Transaction, UserBudget
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class UserScopedRepository(Generic[ModelType]):
    """Generic repository enforcing user_id scoping on all database operations."""

    def __init__(self, model: type[ModelType], db: Session, user_id: str):
        self.model = model
        self.db = db
        self.user_id = str(user_id)
        # Enable RLS on PostgreSQL sessions
        enable_postgres_rls(self.db, self.user_id)

    def get_by_id(self, item_id: str) -> ModelType | None:
        """Fetch a single record by ID, strictly scoped to current user_id."""
        stmt = select(self.model).where(
            self.model.id == item_id,
            self.model.user_id == self.user_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Fetch all records for current user_id."""
        stmt = select(self.model).where(
            self.model.user_id == self.user_id
        ).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, instance: ModelType) -> ModelType:
        """Create a new record, automatically forcing instance.user_id to current user_id."""
        instance.user_id = self.user_id
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def create_many(self, instances: list[ModelType]) -> list[ModelType]:
        """Bulk create records forcing user_id scope."""
        for inst in instances:
            inst.user_id = self.user_id
            self.db.add(inst)
        self.db.commit()
        for inst in instances:
            self.db.refresh(inst)
        return instances

    def delete_by_id(self, item_id: str) -> bool:
        """Delete a record by ID strictly within user_id scope."""
        item = self.get_by_id(item_id)
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False

    def delete_all_user_data(self) -> int:
        """Purge ALL records for this user (DPDP Right to be Forgotten)."""
        stmt = delete(self.model).where(self.model.user_id == self.user_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount


class TransactionRepository(UserScopedRepository[Transaction]):
    def __init__(self, db: Session, user_id: str):
        super().__init__(Transaction, db, user_id)

    def find_by_hash(self, dedup_hash: str) -> Transaction | None:
        stmt = select(Transaction).where(
            Transaction.user_id == self.user_id,
            Transaction.dedup_hash == dedup_hash
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_transactions_in_range(self, start_date, end_date) -> list[Transaction]:
        stmt = select(Transaction).where(
            Transaction.user_id == self.user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).order_by(Transaction.transaction_date.desc())
        return list(self.db.execute(stmt).scalars().all())


class CategoryRuleRepository(UserScopedRepository[CategoryRule]):
    def __init__(self, db: Session, user_id: str):
        super().__init__(CategoryRule, db, user_id)

    def find_matching_rule(self, merchant_name: str) -> CategoryRule | None:
        rules = self.get_all(limit=500)
        merchant_lower = merchant_name.lower()
        for r in rules:
            if r.merchant_pattern.lower() in merchant_lower:
                return r
        return None


class BudgetRepository(UserScopedRepository[UserBudget]):
    def __init__(self, db: Session, user_id: str):
        super().__init__(UserBudget, db, user_id)

    def get_by_category(self, category: str) -> UserBudget | None:
        stmt = select(UserBudget).where(
            UserBudget.user_id == self.user_id,
            UserBudget.category == category
        )
        return self.db.execute(stmt).scalar_one_or_none()
