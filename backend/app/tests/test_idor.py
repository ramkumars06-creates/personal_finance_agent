"""
IDOR Security Verification Tests: Proves tenant isolation and verifies User A cannot access User B's records.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import User, Transaction
from app.repositories.user_scoped_repo import TransactionRepository
from datetime import date


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_user_data_isolation(db_session):
    """
    IDOR Security Test: Verify User A repository instance cannot fetch or delete User B's transaction.
    """
    # Create User A & User B
    user_a = User(email="user_a@example.com", password_hash="hash")
    user_b = User(email="user_b@example.com", password_hash="hash")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # Create Transaction owned by User B
    txn_b = Transaction(
        user_id=user_b.id,
        transaction_date=date.today(),
        encrypted_description="Secret B",
        normalized_merchant="Merchant B",
        amount=1000.0,
        transaction_type="debit",
        category="shopping",
        dedup_hash="hash_b"
    )
    db_session.add(txn_b)
    db_session.commit()

    # Attempt to query User B's transaction using User A's Repository instance
    repo_a = TransactionRepository(db_session, user_a.id)
    
    # 1. Direct ID lookup attempt
    accessed_by_a = repo_a.get_by_id(txn_b.id)
    assert accessed_by_a is None, "IDOR Vulnerability Detected! User A retrieved User B's transaction."

    # 2. Bulk list attempt
    all_a_txns = repo_a.get_all()
    assert len(all_a_txns) == 0, "IDOR Vulnerability! User A listed User B's transactions."

    # 3. Direct delete attempt
    deleted = repo_a.delete_by_id(txn_b.id)
    assert deleted is False, "IDOR Vulnerability! User A deleted User B's transaction."

    # Verify transaction still exists for User B
    repo_b = TransactionRepository(db_session, user_b.id)
    assert repo_b.get_by_id(txn_b.id) is not None
