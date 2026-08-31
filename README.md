# AI Accountant

AI Accountant is a software-only AIML application that converts raw
transaction data into structured double-entry accounting records and
professional financial statements.

## Core Input

The initial supported input format is:

  Date         Transaction                            Amount
  ------------ ------------------------------------ --------
  2026-04-01   Started business with cash             100000
  2026-04-02   Purchased goods from Ram on credit      25000

## Core Workflow

``` text
Excel / CSV
    ↓
File Validation & Normalization
    ↓
AI Transaction Understanding
    ↓
Confidence Scoring
    ↓
Human Review (when required)
    ↓
Validated Accounting Transaction
    ↓
Accounting Engine
    ↓
Journal
    ↓
Ledger
    ↓
Trial Balance
    ↓
Trading A/c
    ↓
P&L A/c
    ↓
Balance Sheet
    ↓
AI Anomaly Detection & Financial Insights
```

## Main Objectives

1.  Understand natural-language accounting transactions.
2.  Convert them into valid debit/credit entries.
3.  Generate Journal, Ledger and Trial Balance automatically.
4.  Generate professional Trading Account, P&L Account and Balance
    Sheet.
5.  Detect ambiguous transactions and request human verification.
6.  Detect unusual accounting behaviour using ML.
7.  Support large transaction files through background processing.
8.  Maintain complete traceability of AI decisions and user corrections.

## Architecture Principle

> AI interprets the transaction. The deterministic accounting engine
> applies accounting rules.

The AI must never directly calculate financial statements. All
accounting outputs must pass deterministic validation.

## Technology Stack

### Frontend

-   Next.js
-   TypeScript
-   Tailwind CSS
-   Responsive desktop/tablet/mobile UI

### Backend

-   FastAPI
-   Python
-   Pydantic
-   SQLAlchemy
-   Alembic

### AIML

-   pandas / NumPy
-   scikit-learn
-   LightGBM / XGBoost
-   Sentence Transformers
-   spaCy
-   Optional PyTorch-based models where justified

### Data

-   PostgreSQL
-   pgvector
-   Redis
-   Celery

### DevOps

-   Docker
-   GitHub Actions
-   Production deployment

## Core AIML Modules

### 1. Transaction Understanding

``` text
Transaction Text
    ↓
Preprocessing
    ↓
Entity Extraction
    ↓
Transaction Classification
    ↓
Account Identification
    ↓
Debit/Credit Prediction
    ↓
Confidence Score
```

### 2. Semantic Matching

Used to find similar historical transactions and improve consistency.

### 3. Anomaly Detection

Uses historical accounting behaviour to identify unusual amounts,
account combinations and transaction patterns.

### 4. Human-in-the-Loop Learning

``` text
AI Prediction
    ↓
User Correction
    ↓
Stored Correction
    ↓
Future Training Data
```

## Accounting Validation Rules

Every journal entry must satisfy:

``` text
Total Debit = Total Credit
```

The financial statements must satisfy:

``` text
Assets = Liabilities + Capital
```

The system must fail safely instead of presenting an invalid Balance
Sheet.

## Frontend Routes

``` text
/login
/dashboard
/upload
/ai-review
/accounting/journal
/accounting/ledger
/accounting/trial-balance
/financial-statements
/insights
/settings
```

## Documentation

-   `PROJECT_ARCHITECTURE.md` --- complete system architecture and phase
    flow
-   `BACKEND_ARCHITECTURE.md` --- backend services, database
    interaction, APIs and frontend integration
-   `FRONTEND_ARCHITECTURE.md` --- pages, components, responsive
    behaviour and frontend state/data flow
-   `DATABASE_INFO.md` --- database schema, tables, relationships,
    indexes and accounting data model

## Development Strategy

Development is phase-driven. Each phase must be implemented, tested and
validated before dependent work is considered complete.

``` text
Foundation
    ↓
Database Model
    ↓
Accounting Engine
    ↓
Dataset Engine
    ↓
AI
    ↓
AI + Accounting Integration
    ↓
Human Review
    ↓
Anomaly Detection
    ↓
Backend APIs
    ↓
Frontend
    ↓
Export
    ↓
Security
    ↓
Performance
    ↓
Testing
    ↓
Deployment
```

## Important Scope Rule

This project is software-only. No hardware is required.

## Project Status

Initial architecture and implementation specification.
