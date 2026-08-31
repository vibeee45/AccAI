# AI Accountant --- Backend Architecture

## 1. Backend Stack

-   FastAPI
-   Python
-   Pydantic
-   SQLAlchemy
-   Alembic
-   PostgreSQL
-   Redis
-   Celery
-   pgvector
-   JWT authentication

## 2. Backend Responsibilities

``` text
API Layer
    ↓
Service Layer
    ↓
Domain / Accounting Layer
    ↓
Data Access Layer
    ↓
PostgreSQL
```

The backend coordinates the AI service, accounting engine, database and
frontend.

## 3. Suggested Backend Structure

``` text
backend/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── companies.py
│   │   ├── uploads.py
│   │   ├── transactions.py
│   │   ├── ai.py
│   │   ├── accounting.py
│   │   ├── insights.py
│   │   ├── anomalies.py
│   │   ├── audit.py
│   │   └── exports.py
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   └── main.py
├── accounting/
│   ├── journal.py
│   ├── ledger.py
│   ├── trial_balance.py
│   ├── trading.py
│   ├── pnl.py
│   └── balance_sheet.py
├── workers/
│   ├── import_worker.py
│   ├── ai_worker.py
│   └── statement_worker.py
└── tests/
```

## 4. API Architecture

### Authentication

``` text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### Companies

``` text
GET    /api/v1/companies
POST   /api/v1/companies
GET    /api/v1/companies/{company_id}
PATCH  /api/v1/companies/{company_id}
```

### Chart of Accounts

``` text
GET    /api/v1/companies/{company_id}/accounts
POST   /api/v1/companies/{company_id}/accounts
PATCH  /api/v1/accounts/{account_id}
DELETE /api/v1/accounts/{account_id}
```

### File Upload

``` text
POST /api/v1/uploads
GET  /api/v1/uploads/{upload_id}
GET  /api/v1/uploads/{upload_id}/progress
POST /api/v1/uploads/{upload_id}/process
```

### Transactions

``` text
GET   /api/v1/transactions
GET   /api/v1/transactions/{transaction_id}
POST  /api/v1/transactions
PATCH /api/v1/transactions/{transaction_id}
```

### AI

``` text
POST /api/v1/ai/classify
POST /api/v1/ai/review/{transaction_id}
POST /api/v1/ai/corrections
GET  /api/v1/ai/predictions/{transaction_id}
```

### Accounting

``` text
GET /api/v1/accounting/journal
GET /api/v1/accounting/ledger
GET /api/v1/accounting/trial-balance
GET /api/v1/accounting/trading
GET /api/v1/accounting/pnl
GET /api/v1/accounting/balance-sheet
```

### Anomalies and Insights

``` text
GET /api/v1/anomalies
GET /api/v1/anomalies/{anomaly_id}
GET /api/v1/insights
```

### Audit

``` text
GET /api/v1/audit
GET /api/v1/audit/{entity_type}/{entity_id}
```

### Export

``` text
POST /api/v1/exports/journal
POST /api/v1/exports/ledger
POST /api/v1/exports/trial-balance
POST /api/v1/exports/trading
POST /api/v1/exports/pnl
POST /api/v1/exports/balance-sheet
GET  /api/v1/exports/{export_id}
```

## 5. API-to-Frontend Connection

``` text
Next.js
   │
   │ HTTPS/REST + JSON
   ▼
FastAPI
   │
   ├── validates request
   ├── authenticates user
   ├── checks company access
   ├── calls service
   └── returns typed response
```

The frontend must never directly access PostgreSQL.

## 6. Excel Processing Flow

``` text
Frontend
   ↓
POST /uploads
   ↓
Backend stores file
   ↓
Creates processing job
   ↓
Redis
   ↓
Celery Worker
   ↓
Read file in chunks
   ↓
Normalize rows
   ↓
AI prediction
   ↓
Accounting validation
   ↓
Persist results
   ↓
Update job progress
```

## 7. AI Integration

The AI layer should return structured data rather than free-form text.

Example:

``` json
{
  "transaction_type": "credit_purchase",
  "debit_account": "Purchases",
  "credit_account": "Ram",
  "amount": 25000,
  "confidence": 0.96
}
```

The accounting service validates this result before posting.

## 8. Service Boundaries

### Transaction Service

Owns raw and normalized transactions.

### AI Service

Owns predictions, embeddings, confidence and model metadata.

### Accounting Service

Owns journal, ledger and financial statements.

### Review Service

Owns human corrections and approvals.

### Anomaly Service

Owns anomaly scores and explanations.

### Audit Service

Owns immutable traceability records.

## 9. Error Handling

The backend should distinguish:

``` text
400 → Invalid input
401 → Authentication failure
403 → Access denied
404 → Resource not found
409 → Accounting/data conflict
422 → Validation failure
429 → Rate limit
500 → Unexpected server error
```

Accounting validation failures should contain actionable information and
must not silently post invalid entries.

## 10. Frontend Integration Contract

All API responses should use consistent structures.

Example:

``` json
{
  "success": true,
  "data": {},
  "message": "Transaction processed successfully"
}
```

Errors:

``` json
{
  "success": false,
  "error": {
    "code": "ACCOUNTING_VALIDATION_FAILED",
    "message": "Debit and credit totals do not match"
  }
}
```

## 11. Backend Completion Criteria

The backend is complete when:

-   All core APIs are implemented.
-   Authentication works.
-   Company-level isolation works.
-   Excel processing is asynchronous.
-   AI predictions are persisted.
-   Accounting outputs are deterministic.
-   APIs are documented.
-   Tests cover critical accounting rules.
-   Frontend can consume all required APIs.
