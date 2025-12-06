# Invoice QC Service 📄✅

A comprehensive Invoice Extraction & Quality Control Service that extracts structured data from PDF invoices and validates them against configurable business rules.

**Author**: [Your Name]  
**Role**: Software Engineer Intern (Data & Development)  
**Completion Status**: ✅ All Core Parts (A-D) + Bonus Frontend (E) Completed

## 📹 Demo Video

**Video Link**: [INSERT YOUR GOOGLE DRIVE LINK HERE]  
*10-20 minute walkthrough covering architecture, code, and live demo*

---

## 🎯 Overview

This project implements a production-ready invoice processing pipeline with:

- **PDF Extraction**: Intelligent extraction of 16+ structured fields from invoice PDFs
- **Quality Control**: 13 comprehensive validation rules across 4 categories
- **CLI Tool**: Command-line interface for batch processing
- **REST API**: FastAPI-based HTTP API for integration
- **Web Console**: React-based QC dashboard (Bonus)

### Completed Components

| Component | Status | Description |
|-----------|--------|-------------|
| Schema Design | ✅ | 16 fields + line items structure |
| Validation Rules | ✅ | 13 rules (4 completeness, 3 format, 4 business, 2 anomaly) |
| PDF Extractor | ✅ | Full extraction with regex/heuristics |
| Validator Core | ✅ | Complete validation engine |
| CLI | ✅ | Extract, validate, full-run commands |
| FastAPI | ✅ | REST endpoints with auto-docs |
| Frontend | ✅ | React QC Console |
| Documentation | ✅ | Comprehensive README + AI notes |
| Tests | ✅ | Pytest unit tests |
| Docker | ✅ | Dockerfile + docker-compose |

---

## 📋 Schema & Validation Design

### Invoice Schema (16 Core Fields)

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `invoice_number` | string | Unique invoice identifier | ✅ |
| `invoice_date` | date | Invoice issue date (YYYY-MM-DD) | ✅ |
| `due_date` | date | Payment due date | ❌ |
| `seller_name` | string | Seller/vendor company name | ✅ |
| `seller_address` | string | Seller's full address | ❌ |
| `seller_vat_id` | string | Seller's VAT/Tax ID | ❌ |
| `buyer_name` | string | Buyer/customer company name | ✅ |
| `buyer_address` | string | Buyer's full address | ❌ |
| `buyer_vat_id` | string | Buyer's VAT/Tax ID | ❌ |
| `currency` | string | Currency code (EUR, USD, etc.) | ✅ |
| `net_total` | decimal | Subtotal before tax | ✅ |
| `tax_amount` | decimal | Total tax amount | ❌ |
| `tax_rate` | decimal | Tax percentage (e.g., 19.0 for 19%) | ❌ |
| `gross_total` | decimal | Final total with tax | ✅ |
| `payment_terms` | string | Payment terms description | ❌ |
| `line_items` | array | List of invoice line items | ❌ |

**Line Item Structure**:
```json
{
  "description": "Product/Service name",
  "quantity": 10.0,
  "unit_price": 5.00,
  "line_total": 50.00
}
```

**Design Rationale**:
- **16 fields** provide comprehensive coverage for B2B invoices
- **Line items included** to enable detailed reconciliation and validation
- **Flexible nullability** allows partial extraction while flagging issues in validation
- **Decimal types** for financial accuracy (avoids floating-point errors)
- **Standardized dates** (YYYY-MM-DD) for consistency and sortability

### Validation Rules (13 Total)

#### 1️⃣ Completeness Rules (4 rules)

| Rule | Description | Rationale |
|------|-------------|-----------|
| `missing_required_field` | invoice_number, invoice_date, seller_name, buyer_name must exist | Core identifiers needed for invoice processing and audit trails |
| `missing_net_total` | net_total must be present | Essential for financial reconciliation |
| `missing_gross_total` | gross_total must be present | Required for payment processing |
| `missing_currency` | currency must be specified | Needed for multi-currency handling and conversion |

#### 2️⃣ Format Rules (3 rules)

| Rule | Description | Rationale |
|------|-------------|-----------|
| `invalid_date_format` | Dates must be YYYY-MM-DD | Ensures parseable, sortable dates; prevents ambiguity (DD/MM vs MM/DD) |
| `invalid_currency` | Currency in [EUR, USD, GBP, INR, JPY, CHF, CAD, AUD] | Limits to commonly supported currencies in financial systems |
| `invalid_numeric_value` | All amounts must be valid decimals | Prevents calculation errors and data corruption |

#### 3️⃣ Business Rules (4 rules)

| Rule | Description | Rationale |
|------|-------------|-----------|
| `invalid_date_sequence` | due_date ≥ invoice_date | Logical date ordering; catches data entry errors |
| `totals_mismatch` | net_total + tax_amount ≈ gross_total (0.5% tolerance) | Catches calculation errors; tolerance accounts for rounding |
| `line_items_sum_mismatch` | Σ(line_items) ≈ net_total (1% tolerance) | Validates itemization accuracy; higher tolerance for multi-step calculations |
| `tax_calculation_mismatch` | tax_amount ≈ net_total × (tax_rate/100) (1% tolerance) | Ensures consistent tax application |

**Tolerance Rationale**: 
- 0.5% for direct calculations (net + tax = gross)
- 1% for multi-step calculations (line items sum, tax rate application)
- Accounts for rounding differences in spreadsheets and accounting systems

#### 4️⃣ Anomaly Rules (2 rules)

| Rule | Description | Rationale |
|------|-------------|-----------|
| `duplicate_invoice` | Unique (invoice_number, seller_name, invoice_date) | Prevents double-processing and payment fraud |
| `negative_amount` | All totals must be ≥ 0 | Flags data corruption or system errors (credit notes handled separately) |

---

## 🏗️ Architecture

### System Flow
```
┌─────────────┐
│   PDF Files │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   Extractor (pdfplumber)        │
│   • Text extraction             │
│   • Regex pattern matching      │
│   • Table parsing               │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Structured JSON               │
│   {invoice_number, dates, ...}  │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Validator Engine              │
│   • Completeness checks         │
│   • Format validation           │
│   • Business rules              │
│   • Anomaly detection           │
└──────┬──────────────────────────┘
       │
       ├──────────────┬─────────────┐
       ▼              ▼             ▼
   ┌───────┐    ┌─────────┐   ┌────────┐
   │  CLI  │    │   API   │   │   UI   │
   └───────┘    └─────────┘   └────────┘
```

### Directory Structure
```
invoice-qc-service/
├── invoice_qc/              # Main package
│   ├── __init__.py
│   ├── models.py            # Pydantic data models
│   ├── extractor.py         # PDF → JSON extraction
│   ├── validator.py         # Validation engine
│   ├── cli.py               # CLI interface
│   └── api/
│       ├── __init__.py
│       └── main.py          # FastAPI application
│
├── frontend/                # React QC Console (Bonus)
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx          # Main QC dashboard
│       ├── main.jsx
│       └── index.css
│
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_validator.py
│   └── test_api.py
│
├── ai-notes/                # AI usage documentation
│   └── README.md
│
├── pdfs/                    # Sample invoice PDFs (place here)
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── .gitignore
├── Dockerfile
└── docker-compose.yml
```

### Module Responsibilities

#### `models.py` - Data Models
- **Purpose**: Define Pydantic schemas for type safety and validation
- **Key Models**: `Invoice`, `LineItem`, `ValidationResult`, `ValidationSummary`
- **Why Pydantic**: 
  - Automatic data validation
  - JSON serialization/deserialization
  - OpenAPI schema generation for FastAPI
  - Type hints for IDE support

#### `extractor.py` - PDF Extraction
- **Purpose**: Parse PDFs into structured JSON
- **Strategy**: 
  - Text extraction via `pdfplumber`
  - Regex patterns for field identification (invoice number, dates, amounts)
  - Heuristic table parsing for line items
  - Multiple pattern fallbacks for robustness
- **Error Handling**: Returns partial data with nulls for missing fields (caught by validator)

#### `validator.py` - Quality Control
- **Purpose**: Apply all 13 validation rules to extracted data
- **Design**: 
  - Modular rule categories (completeness, format, business, anomaly)
  - Per-invoice results + aggregate summary
  - Error counting for analytics and reporting
  - Configurable tolerances for business rules

#### `cli.py` - Command-Line Interface
- **Purpose**: Batch processing tool for automation
- **Commands**:
  - `extract`: PDF → JSON only
  - `validate`: JSON → validation report
  - `full-run`: End-to-end pipeline
- **Features**: 
  - Rich console output with progress indicators
  - Exit codes for CI/CD integration (0 = success, 1 = validation errors)
  - Optional JSON output for debugging

#### `api/main.py` - HTTP API
- **Purpose**: Service integration endpoint for other systems
- **Framework**: FastAPI (chosen for async support, auto-docs, performance)
- **Endpoints**:
  - `GET /health`: Health check
  - `POST /validate-json`: Validate JSON payload
  - `POST /extract-and-validate-pdfs`: Full pipeline via file upload
  - `GET /stats`: Service statistics
- **Features**:
  - CORS enabled for frontend
  - Automatic OpenAPI/Swagger docs at `/docs`
  - Pydantic request/response models

#### `frontend/` - QC Console (Bonus)
- **Purpose**: Internal tool for QC operators to review invoices
- **Tech Stack**: React + Vite + Tailwind CSS
- **Features**:
  - PDF upload or JSON paste modes
  - Real-time validation results
  - Filterable error table (show all / invalid only)
  - Summary statistics dashboard
  - Responsive design

---

## 🚀 Setup & Installation

### Prerequisites

- **Python**: 3.9+ (tested on 3.11)
- **Node.js**: 16+ (for frontend only)
- **Git**: For version control

### Backend Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/invoice-qc-service.git
cd invoice-qc-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m invoice_qc.cli --help
```

**Expected Output**:
```
Usage: python -m invoice_qc.cli [OPTIONS] COMMAND [ARGS]...

  Invoice Quality Control CLI Tool.

Commands:
  extract    Extract invoice data from PDFs.
  full-run   Run full pipeline: extract + validate.
  validate   Validate extracted invoice data.
```

### Frontend Setup (Optional - Bonus)
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Server will run on `http://localhost:3000`

### Docker Setup (Optional)
```bash
# Build and run with docker-compose
docker-compose up --build

# API will be available at http://localhost:8000
# Frontend at http://localhost:3000
```

---

## 📖 Usage

### CLI Examples

#### 1. Extract Only
```bash
python -m invoice_qc.cli extract \
  --pdf-dir ./pdfs \
  --output extracted_invoices.json
```

**Output**:
```
📄 Extracting invoices from: ./pdfs
✅ Extracted 10 invoices → extracted_invoices.json
```

**What it does**: Reads all PDFs in `./pdfs/`, extracts fields, saves to JSON.

#### 2. Validate Only
```bash
python -m invoice_qc.cli validate \
  --input extracted_invoices.json \
  --report validation_report.json
```

**Output**:
```
🔍 Validating invoices from: extracted_invoices.json

==================================================
📊 VALIDATION SUMMARY
==================================================
Total Invoices:   10
✅ Valid:         7
❌ Invalid:       3

🔴 Top Errors:
  • missing_required_field: 3
  • totals_mismatch: 2
  • invalid_date_format: 1

📝 Full report saved to: validation_report.json
```

**What it does**: Loads JSON, runs all validation rules, generates report.

#### 3. Full Pipeline (End-to-End)
```bash
python -m invoice_qc.cli full-run \
  --pdf-dir ./pdfs \
  --report validation_report.json \
  --save-extracted extracted.json
```

**Output**:
```
🚀 Starting full pipeline...

📄 Step 1: Extracting from ./pdfs
✅ Extracted 10 invoices

💾 Saved extracted data → extracted.json

🔍 Step 2: Validating invoices

==================================================
📊 VALIDATION SUMMARY
==================================================
Total Invoices:   10
✅ Valid:         7
❌ Invalid:       3
...
```

**What it does**: Runs extraction AND validation in one command.

---

**(README continues in next message - Reply "continue" for Part 2/2)**
