# AI Accountant --- Frontend Architecture

## 1. Frontend Stack

-   Next.js
-   TypeScript
-   Tailwind CSS
-   Component-based design
-   Responsive desktop/tablet/mobile layouts
-   Typed API client

## 2. Route Architecture

``` text
/login
/register

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

## 3. Main Navigation

``` text
Dashboard
Upload
AI Review

Accounting
├── Journal
├── Ledger
└── Trial Balance

Financial Statements
├── Trading A/c
├── P&L A/c
└── Balance Sheet

AI Insights
Settings
```

## 4. Dashboard

The dashboard should show:

-   Revenue
-   Expenses
-   Gross Profit
-   Net Profit
-   Transaction count
-   Pending AI reviews
-   Anomaly count
-   Revenue/expense trends
-   Important AI insights

The dashboard is a summary, not the place for detailed accounting
tables.

## 5. Upload Page

Flow:

``` text
Select File
    ↓
Validate File
    ↓
Preview Columns
    ↓
Map Columns
    ↓
Confirm Import
    ↓
Processing Progress
    ↓
Import Summary
```

Required columns:

``` text
Date
Transaction
Amount
```

The UI should display:

-   Total rows
-   Valid rows
-   Invalid rows
-   Duplicates
-   AI-readable rows
-   Rows requiring review

## 6. AI Review Page

Each transaction should show:

``` text
Original Statement
Predicted Type
Debit Account
Credit Account
Amount
Confidence
Reason / Supporting Evidence
```

Actions:

``` text
Approve
Edit
Reject
```

Low-confidence entries should be visually prominent.

## 7. Journal Page

Professional table:

``` text
Date | Particulars | Voucher No. | Debit | Credit
```

Features:

-   Date filters
-   Account filters
-   Search
-   Pagination
-   Expandable journal entries
-   Export

## 8. Ledger Page

Account selector:

``` text
Cash A/c
Bank A/c
Purchases A/c
Sales A/c
Ram A/c
```

Table:

``` text
Date | Particulars | Debit | Credit | Balance
```

## 9. Trial Balance Page

Professional presentation:

``` text
Account              Debit              Credit
------------------------------------------------
Cash                 ₹XX
Purchases            ₹XX
Rent                 ₹XX
Capital                                  ₹XX
Sales                                    ₹XX
------------------------------------------------
TOTAL                ₹XX                ₹XX
```

The page must show a clear validation state:

``` text
✓ Trial Balance Balanced
```

or

``` text
✕ Trial Balance Not Balanced
```

## 10. Financial Statements Page

Use one route with tabs:

``` text
[ Trading A/c ] [ P&L A/c ] [ Balance Sheet ]
```

### Trading Account

Show opening stock, purchases, direct expenses, COGS, sales and gross
profit.

### P&L Account

Show gross profit, indirect income, indirect expenses and net profit.

### Balance Sheet

Show liabilities and assets with professional grouping and totals.

These pages should resemble professional accounting statements rather
than generic dashboard cards.

## 11. Responsive Design

### Desktop

Use wide accounting tables with clear debit/credit columns.

### Tablet

Reduce non-essential columns and preserve important accounting
information.

### Mobile

Use:

-   Horizontal scrolling for dense accounting tables where necessary.
-   Expandable rows.
-   Compact account cards.
-   Bottom sheets for filters/actions.
-   Sticky totals where useful.

The mobile UI must be intentionally designed, not merely scaled down.

## 12. Component Architecture

``` text
components/
├── layout/
├── navigation/
├── dashboard/
├── upload/
├── ai-review/
├── accounting/
│   ├── JournalTable
│   ├── LedgerTable
│   ├── TrialBalanceTable
│   └── FinancialStatement
├── insights/
├── forms/
├── tables/
├── charts/
└── feedback/
```

## 13. State and Data Flow

``` text
Page
 ↓
Feature Hook / Server Action
 ↓
Typed API Client
 ↓
FastAPI
 ↓
Response
 ↓
UI State
```

The frontend should not duplicate accounting calculations. It displays
backend-calculated values.

## 14. Loading and Error States

Every data-heavy page must support:

``` text
Loading
Empty
Success
Validation Error
Server Error
Permission Error
```

Large uploads must show processing progress.

## 15. Design Rules

-   Consistent typography.
-   Clear visual hierarchy.
-   Professional financial statement formatting.
-   Strong debit/credit alignment.
-   Clear totals and subtotals.
-   Accessible contrast.
-   Consistent spacing.
-   Responsive interactions.
-   Avoid unnecessary decorative elements.

## 16. Frontend Completion Criteria

The frontend is complete when:

-   All core routes work.
-   All APIs are connected.
-   Desktop layout is polished.
-   Mobile layout is intentionally responsive.
-   Accounting statements are professionally formatted.
-   Upload progress works.
-   AI review works.
-   Errors and empty states are handled.
-   Export actions work.
-   No page contains hard-coded accounting results.
