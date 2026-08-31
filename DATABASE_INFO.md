# AI Accountant --- Database Information

## 1. Database

Primary database:

**PostgreSQL**

Supporting technology:

**pgvector** for semantic transaction embeddings.

## 2. Core Entity Relationship

``` text
User
 │
 └── Company Membership
          │
          ▼
        Company
          │
     ┌────┼─────────────┐
     ▼    ▼             ▼
 Accounts Transactions Financial Periods
              │
              ▼
        Journal Entry
              │
              ▼
         Journal Lines
              │
              ▼
           Ledger
              │
              ▼
       Financial Statements
```

## 3. Main Tables

### users

``` text
id
email
password_hash
name
created_at
updated_at
```

### companies

``` text
id
name
legal_name
currency
financial_year_start
created_at
updated_at
```

### company_users

``` text
id
company_id
user_id
role
created_at
```

### financial_periods

``` text
id
company_id
start_date
end_date
status
```

### chart_of_accounts

``` text
id
company_id
parent_id
code
name
account_type
normal_balance
is_active
created_at
```

Account types:

``` text
ASSET
LIABILITY
EQUITY
INCOME
EXPENSE
```

Normal balance:

``` text
DEBIT
CREDIT
```

## 4. Transactions

### transactions

``` text
id
company_id
financial_period_id
transaction_date
description
amount
source_file_id
source_row_number
status
created_at
updated_at
```

Status examples:

``` text
PENDING
AI_REVIEW
APPROVED
REJECTED
POSTED
FAILED
```

## 5. AI Prediction

### ai_predictions

``` text
id
transaction_id
model_version
transaction_type
debit_account_id
credit_account_id
confidence
prediction_payload
created_at
```

For multi-line accounting entries, the final design may use a separate
prediction-line table rather than limiting the prediction to one debit
and one credit.

## 6. Human Corrections

### ai_corrections

``` text
id
transaction_id
prediction_id
user_id
original_prediction
corrected_prediction
reason
created_at
```

## 7. Journal

### journal_entries

``` text
id
company_id
transaction_id
entry_number
entry_date
description
status
created_at
```

### journal_lines

``` text
id
journal_entry_id
account_id
debit
credit
line_description
created_at
```

Critical constraint:

``` text
debit >= 0
credit >= 0
```

A journal line should not normally have both debit and credit greater
than zero.

## 8. Ledger

Ledger balances should primarily be derived from journal lines rather
than treated as an independent source of truth.

Useful materialized/summary structures can be added later for
performance.

Example derived information:

``` text
account_id
period
debit_total
credit_total
closing_balance
```

## 9. Anomalies

### anomalies

``` text
id
company_id
transaction_id
model_version
anomaly_score
risk_level
explanation
status
created_at
```

Risk levels:

``` text
LOW
MEDIUM
HIGH
CRITICAL
```

## 10. Audit Trail

### audit_logs

``` text
id
company_id
user_id
action
entity_type
entity_id
old_value
new_value
metadata
created_at
```

Important actions include:

``` text
TRANSACTION_CREATED
TRANSACTION_UPDATED
AI_PREDICTION_CREATED
AI_CORRECTION
TRANSACTION_APPROVED
TRANSACTION_REJECTED
JOURNAL_POSTED
EXPORT_CREATED
ACCOUNT_CREATED
```

## 11. Dataset Versioning

### dataset_versions

``` text
id
name
version
source
row_count
checksum
schema_version
created_at
```

### model_versions

``` text
id
model_name
version
dataset_version_id
metrics
artifact_location
created_at
```

This allows us to answer:

``` text
Which model generated this prediction?
Which dataset trained that model?
Which user corrected the prediction?
When was the transaction posted?
```

## 12. Vector Storage

For semantic matching:

``` text
transaction_embeddings
```

Suggested fields:

``` text
id
transaction_id
model_version
embedding
created_at
```

The vector column uses pgvector.

## 13. Important Indexes

Expected high-value indexes:

``` text
transactions(company_id, transaction_date)

transactions(company_id, status)

journal_entries(company_id, entry_date)

journal_lines(account_id)

journal_lines(journal_entry_id)

ai_predictions(transaction_id)

anomalies(company_id, risk_level)

audit_logs(company_id, created_at)
```

Vector indexes should be added after measuring query patterns and
choosing an appropriate pgvector index strategy.

## 14. Multi-Tenant Data Isolation

Every business-owned table must be associated with `company_id` directly
or through a controlled relationship.

Backend queries must always enforce company ownership.

Example:

``` text
SELECT ...
FROM transactions
WHERE id = :transaction_id
AND company_id = :current_company_id;
```

Never trust a company ID supplied only by the frontend.

## 15. Source of Truth

The accounting source of truth is:

``` text
Transactions
    ↓
Journal Entries
    ↓
Journal Lines
```

Ledger and financial statements are derived from validated journal data.

AI predictions are not accounting truth.

## 16. Financial Statement Derivation

``` text
Journal Lines
     ↓
Account Balances
     ↓
Trial Balance
     ↓
Account Classification
     ↓
Trading / P&L / Balance Sheet
```

## 17. Database Integrity Rules

At minimum:

``` text
Debit >= 0
Credit >= 0
Journal Entry Debit Total = Credit Total
Account belongs to same company
Transaction belongs to same company
Journal belongs to same company
Financial period is valid
```

## 18. Future Optimization

Only after profiling:

-   Composite indexes
-   Partitioning for very large transaction tables
-   Materialized summaries
-   Read replicas
-   Connection pooling
-   Bulk inserts
-   Vector index tuning

Do not prematurely add complex database infrastructure.
