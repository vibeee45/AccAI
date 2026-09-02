from enum import Enum


class CompanyRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ACCOUNTANT = "ACCOUNTANT"
    VIEWER = "VIEWER"


class FinancialPeriodStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    LOCKED = "LOCKED"


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class NormalBalance(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    AI_REVIEW = "AI_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    FAILED = "FAILED"


class JournalStatus(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyStatus(str, Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"
    CONFIRMED = "CONFIRMED"