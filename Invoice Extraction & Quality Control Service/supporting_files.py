# ============================================================================
# FILE: tests/test_validator.py
# ============================================================================
"""Unit tests for validation module."""
import pytest
from decimal import Decimal
from invoice_qc.models import Invoice, LineItem
from invoice_qc.validator import InvoiceValidator


class TestCompletenessRules:
    """Test completeness validation rules."""
    
    def test_missing_invoice_number(self):
        invoice = Invoice(
            invoice_date="2024-01-10",
            seller_name="ACME",
            buyer_name="Client",
            currency="EUR",
            net_total=Decimal("100"),
            gross_total=Decimal("119")
        )
        validator = InvoiceValidator()
        results = validator._check_completeness(invoice)
        
        assert len(results) > 0
        assert any("invoice_number" in e.message.lower() for e in results)
    
    def test_all_required_fields_present(self):
        invoice = Invoice(
            invoice_number="INV-001",
            invoice_date="2024-01-10",
            seller_name="ACME Corp",
            buyer_name="Client Ltd",
            currency="EUR",
            net_total=Decimal("100"),
            gross_total=Decimal("119")
        )
        validator = InvoiceValidator()
        results = validator._check_completeness(invoice)
        
        # Should have no completeness errors
        assert len(results) == 0


class TestFormatRules:
    """Test format validation rules."""
    
    def test_invalid_date_format(self):
        invoice = Invoice(
            invoice_number="INV-001",
            invoice_date="01/10/2024",  # Wrong format
            seller_name="ACME",
            buyer_name="Client",
            currency="EUR"
        )
        validator = InvoiceValidator()
        results = validator._check_formats(invoice)
        
        assert any("date" in e.message.lower() for e in results)
    
    def test_invalid_currency(self):
        invoice = Invoice(
            invoice_number="INV-001",
            currency="XYZ"  # Invalid currency
        )
        validator = InvoiceValidator()
        results = validator._check_formats(invoice)
        
        assert any("currency" in e.message.lower() for e in results)


class TestBusinessRules:
    """Test business validation rules."""
    
    def test_due_date_before_invoice_date(self):
        invoice = Invoice(
            invoice_number="INV-001",
            invoice_date="2024-01-20",
            due_date="2024-01-10",  # Before invoice date
            seller_name="ACME",
            buyer_name="Client"
        )
        validator = InvoiceValidator()
        results = validator._check_business_rules(invoice)
        
        assert any("date" in e.message.lower() for e in results)
    
    def test_totals_mismatch(self):
        invoice = Invoice(
            invoice_number="INV-001",
            net_total=Decimal("100"),
            tax_amount=Decimal("19"),
            gross_total=Decimal("200")  # Should be 119
        )
        validator = InvoiceValidator()
        results = validator._check_business_rules(invoice)
        
        assert any("total" in e.message.lower() for e in results)
    
    def test_totals_match_within_tolerance(self):
        invoice = Invoice(
            invoice_number="INV-001",
            net_total=Decimal("100.00"),
            tax_amount=Decimal("19.00"),
            gross_total=Decimal("119.01")  # Within 0.5% tolerance
        )
        validator = InvoiceValidator()
        results = validator._check_business_rules(invoice)
        
        # Should not flag totals_mismatch
        assert not any("mismatch" in e.rule for e in results)


class TestAnomalyRules:
    """Test anomaly detection rules."""
    
    def test_duplicate_detection(self):
        invoices = [
            Invoice(
                invoice_number="INV-001",
                invoice_date="2024-01-10",
                seller_name="ACME Corp",
                buyer_name="Client"
            ),
            Invoice(
                invoice_number="INV-001",
                invoice_date="2024-01-10",
                seller_name="ACME Corp",  # Duplicate
                buyer_name="Another Client"
            )
        ]
        
        validator = InvoiceValidator()
        summary = validator.validate_invoices(invoices)
        
        # Second invoice should have duplicate error
        assert summary.invalid_invoices >= 1
        assert "duplicate" in str(summary.error_counts)
    
    def test_negative_amounts(self):
        invoice = Invoice(
            invoice_number="INV-001",
            net_total=Decimal("-100"),  # Negative
            gross_total=Decimal("119")
        )
        validator = InvoiceValidator()
        seen = set()
        results = validator._check_anomalies(invoice, seen)
        
        assert any("negative" in e.message.lower() for e in results)


# ============================================================================
# FILE: tests/test_api.py
# ============================================================================
"""API endpoint tests."""
import pytest
from fastapi.testclient import TestClient
from invoice_qc.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_validate_json_endpoint():
    """Test JSON validation endpoint."""
    test_invoices = [
        {
            "invoice_number": "INV-001",
            "invoice_date": "2024-01-10",
            "seller_name": "ACME Corp",
            "buyer_name": "Client Ltd",
            "currency": "EUR",
            "net_total": 100.0,
            "gross_total": 119.0
        }
    ]
    
    response = client.post("/validate-json", json=test_invoices)
    assert response.status_code == 200
    
    data = response.json()
    assert "total_invoices" in data
    assert data["total_invoices"] == 1


def test_validate_invalid_json():
    """Test validation with invalid data."""
    invalid_data = [
        {
            "invoice_number": "INV-001"
            # Missing required fields
        }
    ]
    
    response = client.post("/validate-json", json=invalid_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["invalid_invoices"] >= 1


# ============================================================================
# FILE: Dockerfile
# ============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY invoice_qc/ ./invoice_qc/

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run API server
CMD ["uvicorn", "invoice_qc.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ============================================================================
# FILE: .gitignore
# ============================================================================
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# Output files
*.json
*.pdf
extracted_invoices.json
validation_report.json

# Logs
*.log

# Environment
.env
.env.local

# Frontend
node_modules/
dist/
.next/
out/

# OS
.DS_Store
Thumbs.db


# ============================================================================
# FILE: docker-compose.yml
# ============================================================================
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./pdfs:/app/pdfs:ro
      - ./output:/app/output
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - api
    environment:
      - VITE_API_URL=http://localhost:8000


# ============================================================================
# FILE: frontend/package.json
# ============================================================================
{
  "name": "invoice-qc-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24",
    "tailwindcss": "^3.3.2",
    "vite": "^4.3.9"
  }
}


# ============================================================================
# FILE: frontend/vite.config.js
# ============================================================================
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})


# ============================================================================
# FILE: frontend/index.html
# ============================================================================
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Invoice QC Console</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>


# ============================================================================
# FILE: frontend/src/main.jsx
# ============================================================================
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)


# ============================================================================
# FILE: frontend/src/index.css
# ============================================================================
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}


# ============================================================================
# FILE: ai-notes/README.md
# ============================================================================
# AI Usage Documentation

This folder contains documentation of AI tool usage during the project.

## Tools Used

1. **ChatGPT-4** (OpenAI)
2. **GitHub Copilot**
3. **Claude** (Anthropic) - for code review

## Sessions

### Session 1: Schema Design
**Date**: 2024-12-04
**Tool**: ChatGPT-4

**Prompt**: "Design a comprehensive invoice schema for B2B invoices with fields for extraction and validation"

**Output**: Initial schema with 12 fields

**Changes Made**: 
- Extended to 16 fields based on sample PDFs
- Added line_items structure
- Made some fields optional

### Session 2: Regex Pattern Generation
**Date**: 2024-12-04
**Tool**: ChatGPT-4

**Chat Export**: See `session2_regex_patterns.txt`

**Key Learnings**:
- AI patterns were too restrictive
- Needed manual adjustment for real-world variations
- Added case-insensitive matching

### Session 3: Validation Logic
**Tool**: GitHub Copilot

**What Worked**:
- Good suggestions for completeness checks
- Helped with Pydantic model definitions

**What Didn't Work**:
- Business rule logic required manual implementation
- Tolerance calculations needed domain knowledge

## Key Insights

1. ✅ AI is excellent for boilerplate code
2. ✅ Good for suggesting patterns and structures
3. ❌ Lacks domain-specific knowledge
4. ❌ Requires manual testing and refinement

## Examples Where AI Failed

See individual session files for detailed examples.