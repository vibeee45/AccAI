from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ai_prediction import AIPrediction
from app.models.anomaly import Anomaly
from app.models.audit_log import AuditLog
from app.models.enums import (
    AnomalyStatus,
    FinancialPeriodStatus,
    RiskLevel,
)
from app.models.user import User

from app.schemas.account import AccountCreate
from app.schemas.company import CompanyCreate
from app.schemas.financial_period import FinancialPeriodCreate
from app.schemas.journal import JournalEntryCreate, JournalLineCreate
from app.schemas.transaction import TransactionCreate

from app.services.account_service import AccountService
from app.services.company_service import CompanyService
from app.services.financial_period_service import FinancialPeriodService
from app.services.journal_service import JournalService
from app.services.transaction_service import TransactionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_user(db):
    user = User(
        email="test@accai.com",
        password_hash="hashed-password",
        name="Test User",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_company(db, user):
    company_service = CompanyService(db)

    company = company_service.create_company(
        CompanyCreate(
            name="ACCAI Test Company",
            legal_name="ACCAI Test Company Pvt Ltd",
            currency="INR",
            financial_year_start="2026-04-01",
        ),
        user.id,
    )

    return company


def create_financial_period(db, company):
    period_service = FinancialPeriodService(db)

    period = period_service.create_period(
        FinancialPeriodCreate(
            company_id=company.id,
            start_date="2026-04-01",
            end_date="2027-03-31",
            status=FinancialPeriodStatus.OPEN,
        )
    )

    return period


def create_account(
    db,
    company_id,
    code,
    name,
    account_type,
    normal_balance,
):
    account_service = AccountService(db)

    return account_service.create_account(
        AccountCreate(
            company_id=company_id,
            code=code,
            name=name,
            account_type=account_type,
            normal_balance=normal_balance,
        )
    )


def create_transaction(
    db,
    company_id,
    financial_period_id,
    description="Test transaction",
    amount=Decimal("10000.00"),
):
    transaction_service = TransactionService(db)

    return transaction_service.create_transaction(
        TransactionCreate(
            company_id=company_id,
            financial_period_id=financial_period_id,
            transaction_date="2026-04-10",
            description=description,
            amount=amount,
        )
    )


# ---------------------------------------------------------------------------
# 1. Complete accounting flow
# ---------------------------------------------------------------------------


def test_complete_accounting_flow(db):
    user = create_user(db)

    company = create_company(
        db,
        user,
    )

    period = create_financial_period(
        db,
        company,
    )

    cash_account = create_account(
        db,
        company.id,
        "1000",
        "Cash",
        "ASSET",
        "DEBIT",
    )

    capital_account = create_account(
        db,
        company.id,
        "3000",
        "Capital",
        "EQUITY",
        "CREDIT",
    )

    transaction = create_transaction(
        db,
        company.id,
        period.id,
        description="Owner introduced capital in cash",
        amount=Decimal("10000.00"),
    )

    journal_service = JournalService(db)

    journal = journal_service.create_entry(
        JournalEntryCreate(
            company_id=company.id,
            transaction_id=transaction.id,
            entry_date="2026-04-10",
            description="Capital introduced",
            lines=[
                JournalLineCreate(
                    account_id=cash_account.id,
                    debit=Decimal("10000.00"),
                    credit=Decimal("0.00"),
                    line_description="Cash received",
                ),
                JournalLineCreate(
                    account_id=capital_account.id,
                    debit=Decimal("0.00"),
                    credit=Decimal("10000.00"),
                    line_description="Capital introduced",
                ),
            ],
        )
    )

    assert journal.id is not None
    assert journal.company_id == company.id
    assert journal.transaction_id == transaction.id

    db.refresh(transaction)

    assert transaction.id is not None


# ---------------------------------------------------------------------------
# 2. Transaction outside financial period rejected
# ---------------------------------------------------------------------------


def test_transaction_outside_financial_period_is_rejected(db):
    user = create_user(db)
    company = create_company(db, user)
    period = create_financial_period(db, company)

    transaction_service = TransactionService(db)

    # Valid transaction inside the period
    transaction = transaction_service.create_transaction(
        TransactionCreate(
            company_id=company.id,
            financial_period_id=period.id,
            transaction_date="2026-04-10",
            description="Inside period transaction",
            amount=Decimal("1000.00"),
        )
    )

    assert transaction.id is not None

    # Invalid transaction outside the period
    with pytest.raises(ValueError):
        transaction_service.create_transaction(
            TransactionCreate(
                company_id=company.id,
                financial_period_id=period.id,
                transaction_date="2028-01-01",
                description="Outside period",
                amount=Decimal("1000.00"),
            )
        )


# ---------------------------------------------------------------------------
# 3. Duplicate account code rejected
# ---------------------------------------------------------------------------


def test_duplicate_account_code_rejected(db):
    user = create_user(db)
    company = create_company(db, user)

    account_service = AccountService(db)

    account_service.create_account(
        AccountCreate(
            company_id=company.id,
            code="1000",
            name="Cash",
            account_type="ASSET",
            normal_balance="DEBIT",
        )
    )

    with pytest.raises(ValueError):
        account_service.create_account(
            AccountCreate(
                company_id=company.id,
                code="1000",
                name="Another Cash",
                account_type="ASSET",
                normal_balance="DEBIT",
            )
        )


# ---------------------------------------------------------------------------
# 4. Overlapping financial period rejected
# ---------------------------------------------------------------------------


def test_overlapping_financial_period_rejected(db):
    user = create_user(db)
    company = create_company(db, user)

    period_service = FinancialPeriodService(db)

    # First financial period already exists.
    first_period = period_service.create_period(
        FinancialPeriodCreate(
            company_id=company.id,
            start_date="2026-04-01",
            end_date="2027-03-31",
            status=FinancialPeriodStatus.OPEN,
        )
    )

    assert first_period.id is not None
    assert first_period.company_id == company.id

    # This second period overlaps with the first one.
    with pytest.raises(ValueError):
        period_service.create_period(
            FinancialPeriodCreate(
                company_id=company.id,
                start_date="2026-10-01",
                end_date="2027-03-31",
                status=FinancialPeriodStatus.OPEN,
            )
        )


# ---------------------------------------------------------------------------
# 5. Closed financial period rejects transaction
# ---------------------------------------------------------------------------


def test_closed_period_rejects_transaction(db):
    user = create_user(db)
    company = create_company(db, user)

    period_service = FinancialPeriodService(db)

    period = period_service.create_period(
        FinancialPeriodCreate(
            company_id=company.id,
            start_date="2026-04-01",
            end_date="2027-03-31",
            status=FinancialPeriodStatus.CLOSED,
        )
    )

    transaction_service = TransactionService(db)

    with pytest.raises(ValueError):
        transaction_service.create_transaction(
            TransactionCreate(
                company_id=company.id,
                financial_period_id=period.id,
                transaction_date="2026-04-10",
                description="Closed period transaction",
                amount=Decimal("1000.00"),
            )
        )


# ---------------------------------------------------------------------------
# 6. Cross-company account rejected
# ---------------------------------------------------------------------------


def test_cross_company_account_rejected(db):
    user = create_user(db)

    company_1 = create_company(
        db,
        user,
    )

    # Create second company using the service directly.
    company_2_service = CompanyService(db)

    company_2 = company_2_service.create_company(
        CompanyCreate(
            name="Second Test Company",
            legal_name="Second Test Company Pvt Ltd",
            currency="INR",
            financial_year_start="2026-04-01",
        ),
        user.id,
    )

    period = create_financial_period(
        db,
        company_1,
    )

    account = create_account(
        db,
        company_2.id,
        "1000",
        "Cash",
        "ASSET",
        "DEBIT",
    )

    transaction = create_transaction(
        db,
        company_1.id,
        period.id,
    )

    journal_service = JournalService(db)

    with pytest.raises(ValueError):
        journal_service.create_entry(
            JournalEntryCreate(
                company_id=company_1.id,
                transaction_id=transaction.id,
                entry_date="2026-04-10",
                description="Cross company test",
                lines=[
                    JournalLineCreate(
                        account_id=account.id,
                        debit=Decimal("1000.00"),
                        credit=Decimal("0.00"),
                    ),
                    JournalLineCreate(
                        account_id=account.id,
                        debit=Decimal("0.00"),
                        credit=Decimal("1000.00"),
                    ),
                ],
            )
        )


# ---------------------------------------------------------------------------
# 7. AI prediction can be stored against transaction
# ---------------------------------------------------------------------------


def test_ai_prediction_can_be_stored_against_transaction(db):
    user = create_user(db)
    company = create_company(db, user)
    period = create_financial_period(db, company)

    transaction = create_transaction(
        db,
        company.id,
        period.id,
        description="Paid electricity bill",
        amount=Decimal("2500.00"),
    )

    prediction = AIPrediction(
        transaction_id=transaction.id,
        model_version="test-model-v1",
        transaction_type="UTILITY_EXPENSE",
        confidence=Decimal("0.9500"),
        prediction_payload={
            "description": "Paid electricity bill",
            "classification": "Electricity Expense",
        },
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    assert prediction.id is not None
    assert prediction.transaction_id == transaction.id
    assert prediction.model_version == "test-model-v1"
    assert prediction.confidence == Decimal("0.9500")


# ---------------------------------------------------------------------------
# 8. AI prediction confidence constraint
# ---------------------------------------------------------------------------


def test_ai_prediction_confidence_constraint(db):
    user = create_user(db)
    company = create_company(db, user)
    period = create_financial_period(db, company)

    transaction = create_transaction(
        db,
        company.id,
        period.id,
    )

    prediction = AIPrediction(
        transaction_id=transaction.id,
        model_version="test-model-v1",
        transaction_type="EXPENSE",
        confidence=Decimal("1.5000"),
        prediction_payload={},
    )

    db.add(prediction)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ---------------------------------------------------------------------------
# 9. Anomaly can be stored against transaction
# ---------------------------------------------------------------------------


def test_anomaly_can_be_stored_against_transaction(db):
    user = create_user(db)
    company = create_company(db, user)
    period = create_financial_period(db, company)

    transaction = create_transaction(
        db,
        company.id,
        period.id,
        description="Unusual transaction",
        amount=Decimal("99999.00"),
    )

    anomaly = Anomaly(
        company_id=company.id,
        transaction_id=transaction.id,
        model_version="anomaly-model-v1",
        anomaly_score=Decimal("0.980000"),
        risk_level=RiskLevel.HIGH,
        explanation="Transaction amount is significantly higher than normal.",
        status=AnomalyStatus.OPEN,
    )

    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    assert anomaly.id is not None
    assert anomaly.transaction_id == transaction.id
    assert anomaly.company_id == company.id
    assert anomaly.risk_level == RiskLevel.HIGH
    assert anomaly.status == AnomalyStatus.OPEN


# ---------------------------------------------------------------------------
# 10. Anomaly risk levels and statuses
# ---------------------------------------------------------------------------


def test_anomaly_risk_levels_and_statuses(db):
    user = create_user(db)
    company = create_company(db, user)
    period = create_financial_period(db, company)

    transaction = create_transaction(
        db,
        company.id,
        period.id,
        description="Risk level test",
        amount=Decimal("5000.00"),
    )

    anomaly = Anomaly(
        company_id=company.id,
        transaction_id=transaction.id,
        model_version="anomaly-model-v1",
        anomaly_score=Decimal("0.750000"),
        risk_level=RiskLevel.MEDIUM,
        explanation="Medium risk transaction.",
        status=AnomalyStatus.OPEN,
    )

    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    assert anomaly.risk_level == RiskLevel.MEDIUM
    assert anomaly.status == AnomalyStatus.OPEN

    anomaly.risk_level = RiskLevel.CRITICAL
    anomaly.status = AnomalyStatus.CONFIRMED

    db.commit()
    db.refresh(anomaly)

    assert anomaly.risk_level == RiskLevel.CRITICAL
    assert anomaly.status == AnomalyStatus.CONFIRMED


# ---------------------------------------------------------------------------
# 11. Audit log captures old/new values and metadata
# ---------------------------------------------------------------------------


def test_audit_log_captures_old_new_values_and_metadata(db):
    user = create_user(db)
    company = create_company(db, user)
    period = create_financial_period(db, company)

    transaction = create_transaction(
        db,
        company.id,
        period.id,
        description="Original transaction",
        amount=Decimal("1000.00"),
    )

    audit = AuditLog(
        company_id=company.id,
        user_id=user.id,
        action="UPDATE",
        entity_type="TRANSACTION",
        entity_id=transaction.id,
        old_value={
            "amount": "1000.00",
            "description": "Old description",
        },
        new_value={
            "amount": "1500.00",
            "description": "Updated description",
        },
        extra_metadata={
            "source": "integration-test",
            "reason": "correction",
        },
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    assert audit.id is not None
    assert audit.company_id == company.id
    assert audit.user_id == user.id
    assert audit.action == "UPDATE"
    assert audit.entity_type == "TRANSACTION"
    assert audit.entity_id == transaction.id

    assert audit.old_value["amount"] == "1000.00"
    assert audit.old_value["description"] == "Old description"

    assert audit.new_value["amount"] == "1500.00"
    assert audit.new_value["description"] == "Updated description"

    assert audit.extra_metadata["source"] == "integration-test"
    assert audit.extra_metadata["reason"] == "correction"


# ---------------------------------------------------------------------------
# 12. AI prediction foreign key enforced
# ---------------------------------------------------------------------------


def test_ai_prediction_foreign_key_enforced(db):
    user = create_user(db)
    company = create_company(db, user)

    fake_transaction_id = "00000000-0000-0000-0000-000000000001"

    prediction = AIPrediction(
        transaction_id=fake_transaction_id,
        model_version="test-model-v1",
        transaction_type="EXPENSE",
        confidence=Decimal("0.9000"),
        prediction_payload={},
    )

    db.add(prediction)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ---------------------------------------------------------------------------
# 13. Anomaly foreign key enforced
# ---------------------------------------------------------------------------


def test_anomaly_foreign_key_enforced(db):
    user = create_user(db)
    company = create_company(db, user)

    fake_transaction_id = "00000000-0000-0000-0000-000000000002"

    anomaly = Anomaly(
        company_id=company.id,
        transaction_id=fake_transaction_id,
        model_version="anomaly-model-v1",
        anomaly_score=Decimal("0.900000"),
        risk_level=RiskLevel.HIGH,
        explanation="Foreign key test.",
        status=AnomalyStatus.OPEN,
    )

    db.add(anomaly)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()