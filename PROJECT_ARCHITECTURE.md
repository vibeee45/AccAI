# AI Accountant --- Project Architecture

## 1. System Overview

``` text
                         USER
                          │
                          ▼
                 Next.js Frontend
                          │
                       REST API
                          │
                          ▼
                  FastAPI Backend
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   PostgreSQL          Redis/Celery      AI/ML Layer
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                 Accounting Engine
                          │
                          ▼
              Financial Statements
```

## 2. Core Architectural Principle

The system has four major responsibilities:

1.  AI/ML --- understand transaction meaning.
2.  Accounting Engine --- apply deterministic accounting rules.
3.  Database --- store the accounting source of truth.
4.  Frontend --- present results and provide human verification.

## 3. End-to-End Transaction Flow

``` text
Excel / CSV
    ↓
Upload Validation
    ↓
Normalization
    ↓
Background Processing
    ↓
AI Transaction Understanding
    ↓
Structured Transaction
    ↓
Confidence Check
    ├── High → Automatic processing
    └── Low  → Human Review
                  ↓
             User Correction
                  ↓
          Validated Transaction
                  ↓
            Accounting Engine
                  ↓
              Journal Entry
                  ↓
                Ledger
                  ↓
            Trial Balance
                  ↓
       ┌──────────┴──────────┐
       ↓                     ↓
  Trading A/c              P&L A/c
       └──────────┬──────────┘
                  ↓
           Balance Sheet
                  ↓
        Anomaly Detection
                  ↓
          AI Financial Insights
```

## 4. Major Implementation Phases

### Phase 0 --- Project Foundation

-   0.1 Repository and Git setup
-   0.2 Project structure
-   0.3 Environment configuration
-   0.4 Docker setup
-   0.5 PostgreSQL
-   0.6 Redis
-   0.7 Backend initialization
-   0.8 Frontend initialization
-   0.9 CI/CD

### Phase 1 --- Database & Accounting Model

-   1.1 Users
-   1.2 Companies
-   1.3 Financial years
-   1.4 Chart of accounts
-   1.5 Transactions
-   1.6 Journal entries
-   1.7 Journal lines
-   1.8 AI predictions
-   1.9 Corrections
-   1.10 Anomalies
-   1.11 Audit records
-   1.12 Constraints and indexes

### Phase 2 --- Accounting Engine

-   2.1 Normalization
-   2.2 Double-entry validation
-   2.3 Journal generation
-   2.4 Ledger posting
-   2.5 Trial Balance
-   2.6 Trading Account
-   2.7 P&L
-   2.8 Balance Sheet
-   2.9 Reconciliation
-   2.10 Automated tests

### Phase 3 --- Dataset Engine

-   3.1 Public data collection
-   3.2 Cleaning
-   3.3 Accounting templates
-   3.4 Transaction generation
-   3.5 Account combinations
-   3.6 Natural-language variations
-   3.7 Validation
-   3.8 Deduplication
-   3.9 Train/validation/test split
-   3.10 Dataset versioning
-   3.11 Large-scale generation

### Phase 4 --- AI Transaction Understanding

-   4.1 Text preprocessing
-   4.2 Entity extraction
-   4.3 Transaction classification
-   4.4 Account identification
-   4.5 Debit/credit prediction
-   4.6 Payment-mode detection
-   4.7 Embeddings
-   4.8 Semantic matching
-   4.9 Confidence scoring
-   4.10 Evaluation
-   4.11 Model versioning

### Phase 5 --- AI + Accounting Integration

-   5.1 Prediction schema
-   5.2 Structured output
-   5.3 AI-to-accounting adapter
-   5.4 Journal generation
-   5.5 Rule validation
-   5.6 Failure handling
-   5.7 Confidence routing
-   5.8 End-to-end tests

### Phase 6 --- Human-in-the-Loop

-   6.1 Review queue
-   6.2 Low-confidence detection
-   6.3 Transaction editing
-   6.4 Approve/reject
-   6.5 Correction storage
-   6.6 Feedback dataset

### Phase 7 --- AI Anomaly Detection

-   7.1 Feature engineering
-   7.2 Historical behaviour
-   7.3 Amount deviation
-   7.4 Account-pair analysis
-   7.5 Isolation Forest baseline
-   7.6 Model experiments
-   7.7 Anomaly scoring
-   7.8 Risk classification
-   7.9 Explanations

### Phase 8 --- Audit & Traceability

-   8.1 Dataset version history
-   8.2 User action logs
-   8.3 AI decision logs
-   8.4 Transaction modification history
-   8.5 Approval/rejection history
-   8.6 Model version tracking
-   8.7 Audit Trail API
-   8.8 Audit viewer
-   8.9 Immutable audit records

### Phase 9 --- File Processing

-   9.1 Excel upload
-   9.2 CSV upload
-   9.3 File validation
-   9.4 Column mapping
-   9.5 Row validation
-   9.6 Duplicate detection
-   9.7 Chunk processing
-   9.8 Background jobs
-   9.9 Progress tracking
-   9.10 Import summary

### Phase 10 --- Backend APIs

Authentication, company, chart-of-accounts, upload, transaction, AI,
accounting, anomaly, insight, audit and export APIs.

### Phase 11 --- Financial Intelligence

Revenue, expense, profit, ratio, receivable, payable, trend and
period-comparison analysis.

### Phase 12 --- Frontend Foundation

Design system, typography, components, navigation, forms, tables,
responsive breakpoints and states.

### Phase 13 --- Frontend Pages

Login, dashboard, upload, AI review, journal, ledger, trial balance,
financial statements, insights and settings.

### Phase 14 --- Professional Accounting UI

Professional Trading A/c, P&L A/c and Balance Sheet layouts with correct
debit/credit presentation, subtotals, totals and print-friendly
formatting.

### Phase 15 --- Responsive Mobile Design

Mobile navigation, accounting tables, financial statements, review flows
and tablet optimization.

### Phase 16 --- Export

Excel/PDF export for journal, ledger, trial balance and financial
statements.

### Phase 17 --- Security

Authentication, authorization, company isolation, secure uploads,
validation, rate limiting and audit protection.

### Phase 18 --- Performance

Indexes, pagination, batch processing, background workers, caching,
vector indexes, ML inference optimization and million-row benchmarks.

### Phase 19 --- Testing

Unit, accounting, ML, API, integration, E2E, performance, mobile and
security tests.

### Phase 20 --- Deployment

Production Docker, databases, Redis, ML workers, backend, frontend,
HTTPS, backups and smoke tests.

### Phase 21 --- Documentation & Portfolio

README, architecture diagrams, ER diagram, ML documentation, dataset
documentation, model evaluation, API documentation, benchmarks,
screenshots and demo.

## 5. Golden Rules

-   AI may suggest; accounting rules decide.
-   Every posted journal must balance.
-   Every financial statement must be validated.
-   Low-confidence AI predictions must be reviewable.
-   Every important user/AI change must be traceable.
-   Large files must be processed asynchronously.
-   No company may access another company's data.
