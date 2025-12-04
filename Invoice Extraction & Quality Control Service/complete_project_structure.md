# Invoice QC Service - Complete Implementation Guide

This document provides the complete project structure and all necessary files for your Invoice Extraction & Quality Control Service.

## 📁 Project Structure

```
invoice-qc-service/
├── invoice_qc/
│   ├── __init__.py
│   ├── extractor.py          # PDF extraction logic
│   ├── validator.py          # Validation rules and logic
│   ├── cli.py                # Command-line interface
│   ├── models.py             # Data models/schemas
│   └── api/
│       ├── __init__.py
│       └── main.py           # FastAPI application
├── frontend/                  # Bonus: React QC Console
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── App.jsx
│       └── main.jsx
├── pdfs/                     # Sample invoice PDFs
├── tests/                    # Unit tests
├── ai-notes/                 # AI usage documentation
├── requirements.txt
├── README.md
├── .gitignore
└── Dockerfile (optional)
```

## 🎯 Schema & Validation Design

### Invoice Schema (12 fields)

**Core Fields:**
1. `invoice_number` (string) - Unique invoice identifier
2. `invoice_date` (date) - Date invoice was issued
3. `due_date` (date) - Payment due date
4. `seller_name` (string) - Seller/vendor company name
5. `seller_address` (string) - Seller's address
6. `seller_vat_id` (string) - Seller's VAT/Tax ID
7. `buyer_name` (string) - Buyer/customer company name
8. `buyer_address` (string) - Buyer's address
9. `buyer_vat_id` (string) - Buyer's VAT/Tax ID
10. `currency` (string) - Currency code (EUR, USD, INR, etc.)
11. `net_total` (decimal) - Subtotal before tax
12. `tax_amount` (decimal) - Total tax amount
13. `tax_rate` (decimal) - Tax percentage applied
14. `gross_total` (decimal) - Final total with tax
15. `payment_terms` (string) - Payment terms description
16. `line_items` (array) - List of invoice line items

**Line Item Fields:**
- `description` (string) - Item/service description
- `quantity` (decimal) - Quantity ordered
- `unit_price` (decimal) - Price per unit
- `line_total` (decimal) - Line subtotal

### Validation Rules

**Completeness Rules (4):**
1. **Required Fields** - invoice_number, invoice_date, seller_name, buyer_name must be non-empty
2. **Required Amounts** - net_total, gross_total must exist and be numeric
3. **Currency Presence** - currency field must be specified
4. **Date Completeness** - invoice_date must be present

**Format Rules (3):**
1. **Date Format** - Dates must be valid and parseable (YYYY-MM-DD)
2. **Currency Validation** - Currency must be in [EUR, USD, GBP, INR, JPY, CHF, CAD, AUD]
3. **Numeric Values** - All monetary amounts must be valid numbers

**Business Rules (4):**
1. **Date Logic** - due_date must be on or after invoice_date
2. **Total Calculation** - net_total + tax_amount ≈ gross_total (within 0.5% tolerance)
3. **Line Item Sum** - Sum of line_items.line_total ≈ net_total (within 1% tolerance)
4. **Tax Rate Consistency** - tax_amount ≈ net_total × (tax_rate/100) when tax_rate present

**Anomaly Rules (2):**
1. **Duplicate Detection** - No duplicate invoices (same invoice_number + seller_name + invoice_date)
2. **Negative Values** - Totals must be non-negative

---

## 📄 File Contents

### 1. requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pdfplumber==0.10.3
python-multipart==0.0.6
click==8.1.7
python-dateutil==2.8.2
pytest==7.4.3
httpx==0.25.2
```

### 2. invoice_qc/models.py

```python
"""Data models for invoice extraction and validation."""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Represents a single line item on an invoice."""
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class Invoice(BaseModel):
    """Represents a complete invoice with all extracted fields."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    seller_name: Optional[str] = None
    seller_address: Optional[str] = None
    seller_vat_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_vat_id: Optional[str] = None
    currency: Optional[str] = None
    net_total: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    gross_total: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    source_file: Optional[str] = None


class ValidationError(BaseModel):
    """Represents a single validation error."""
    rule: str
    message: str


class ValidationResult(BaseModel):
    """Validation result for a single invoice."""
    invoice_id: str
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)


class ValidationSummary(BaseModel):
    """Summary of validation results across all invoices."""
    total_invoices: int
    valid_invoices: int
    invalid_invoices: int
    error_counts: dict = Field(default_factory=dict)
    validation_results: List[ValidationResult] = Field(default_factory=list)
```

### 3. invoice_qc/extractor.py

```python
"""PDF extraction module for invoices."""
import re
import pdfplumber
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime

from .models import Invoice, LineItem


class InvoiceExtractor:
    """Extracts structured data from invoice PDFs."""
    
    # Common patterns for invoice fields
    INVOICE_NUMBER_PATTERNS = [
        r'Invoice\s+(?:Number|No\.?|#)\s*:?\s*([A-Z0-9-]+)',
        r'Invoice\s+([A-Z0-9-]+)',
        r'INV[-#]?\s*([A-Z0-9-]+)',
    ]
    
    DATE_PATTERNS = [
        r'Invoice\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}\.\d{1,2}\.\d{4})',
    ]
    
    DUE_DATE_PATTERNS = [
        r'Due\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Payment\s+Due\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    
    AMOUNT_PATTERNS = {
        'net_total': [r'Subtotal\s*:?\s*([€$£¥]?[\d,]+\.?\d*)', r'Net\s+Total\s*:?\s*([€$£¥]?[\d,]+\.?\d*)'],
        'tax_amount': [r'(?:VAT|Tax)\s*:?\s*([€$£¥]?[\d,]+\.?\d*)'],
        'gross_total': [r'Total\s*:?\s*([€$£¥]?[\d,]+\.?\d*)', r'Grand\s+Total\s*:?\s*([€$£¥]?[\d,]+\.?\d*)'],
    }
    
    CURRENCY_MAP = {
        '€': 'EUR', '$': 'USD', '£': 'GBP', '¥': 'JPY',
        'EUR': 'EUR', 'USD': 'USD', 'GBP': 'GBP', 'INR': 'INR',
        'JPY': 'JPY', 'CHF': 'CHF', 'CAD': 'CAD', 'AUD': 'AUD'
    }

    def extract_from_directory(self, pdf_dir: str) -> List[Invoice]:
        """Extract invoices from all PDFs in a directory."""
        pdf_path = Path(pdf_dir)
        invoices = []
        
        for pdf_file in pdf_path.glob('*.pdf'):
            try:
                invoice = self.extract_from_pdf(str(pdf_file))
                invoices.append(invoice)
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
                # Create empty invoice with source file for tracking
                invoice = Invoice(source_file=pdf_file.name)
                invoices.append(invoice)
        
        return invoices

    def extract_from_pdf(self, pdf_path: str) -> Invoice:
        """Extract structured invoice data from a single PDF."""
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            full_text = ""
            tables = []
            
            for page in pdf.pages:
                full_text += page.extract_text() or ""
                # Extract tables for line items
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
            
            # Extract fields
            invoice = Invoice(source_file=Path(pdf_path).name)
            
            invoice.invoice_number = self._extract_invoice_number(full_text)
            invoice.invoice_date = self._extract_date(full_text, self.DATE_PATTERNS)
            invoice.due_date = self._extract_date(full_text, self.DUE_DATE_PATTERNS)
            
            # Extract parties
            invoice.seller_name = self._extract_party(full_text, "seller")
            invoice.buyer_name = self._extract_party(full_text, "buyer")
            invoice.seller_vat_id = self._extract_vat_id(full_text, "seller")
            invoice.buyer_vat_id = self._extract_vat_id(full_text, "buyer")
            
            # Extract amounts
            invoice.currency = self._extract_currency(full_text)
            invoice.net_total = self._extract_amount(full_text, 'net_total')
            invoice.tax_amount = self._extract_amount(full_text, 'tax_amount')
            invoice.gross_total = self._extract_amount(full_text, 'gross_total')
            invoice.tax_rate = self._extract_tax_rate(full_text)
            
            # Extract line items from tables
            invoice.line_items = self._extract_line_items(tables)
            
            return invoice

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text."""
        for pattern in self.INVOICE_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_date(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract and normalize date from text."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Try to parse and normalize date
                try:
                    # Handle various date formats
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y', '%d.%m.%Y']:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            return dt.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                except Exception:
                    pass
        return None

    def _extract_party(self, text: str, party_type: str) -> Optional[str]:
        """Extract seller or buyer name."""
        if party_type == "seller":
            patterns = [
                r'From\s*:?\s*([A-Za-z0-9\s&.,]+?)(?:\n|Address)',
                r'Seller\s*:?\s*([A-Za-z0-9\s&.,]+?)(?:\n)',
                r'Vendor\s*:?\s*([A-Za-z0-9\s&.,]+?)(?:\n)',
            ]
        else:
            patterns = [
                r'To\s*:?\s*([A-Za-z0-9\s&.,]+?)(?:\n|Address)',
                r'Buyer\s*:?\s*([A-Za-z0-9\s&.,]+?)(?:\n)',
                r'Customer\s*:?\s*([A-Za-z0-9\s&.,]+?)(?:\n)',
            ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                return name if len(name) > 2 else None
        return None

    def _extract_vat_id(self, text: str, party_type: str) -> Optional[str]:
        """Extract VAT/Tax ID."""
        patterns = [
            r'VAT\s*(?:ID|No\.?|Number)\s*:?\s*([A-Z0-9-]+)',
            r'Tax\s*ID\s*:?\s*([A-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_currency(self, text: str) -> Optional[str]:
        """Extract currency code."""
        # Look for currency symbols or codes
        for symbol, code in self.CURRENCY_MAP.items():
            if symbol in text:
                return code
        return None

    def _extract_amount(self, text: str, amount_type: str) -> Optional[Decimal]:
        """Extract monetary amount."""
        patterns = self.AMOUNT_PATTERNS.get(amount_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                # Clean amount string
                amount_str = re.sub(r'[€$£¥,]', '', amount_str)
                try:
                    return Decimal(amount_str)
                except (InvalidOperation, ValueError):
                    pass
        return None

    def _extract_tax_rate(self, text: str) -> Optional[Decimal]:
        """Extract tax rate percentage."""
        patterns = [
            r'VAT\s*@?\s*(\d+(?:\.\d+)?)\s*%',
            r'Tax\s*Rate\s*:?\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*VAT',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return Decimal(match.group(1))
                except (InvalidOperation, ValueError):
                    pass
        return None

    def _extract_line_items(self, tables: List[List[List[str]]]) -> List[LineItem]:
        """Extract line items from extracted tables."""
        line_items = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Try to identify header row
            headers = [str(h).lower() if h else '' for h in table[0]]
            
            # Look for description, quantity, price columns
            desc_idx = self._find_column_index(headers, ['description', 'item', 'product'])
            qty_idx = self._find_column_index(headers, ['quantity', 'qty', 'amount'])
            price_idx = self._find_column_index(headers, ['price', 'unit price', 'rate'])
            total_idx = self._find_column_index(headers, ['total', 'amount', 'line total'])
            
            # Process data rows
            for row in table[1:]:
                if not row or len(row) < 2:
                    continue
                
                try:
                    description = row[desc_idx] if desc_idx is not None else row[0]
                    quantity = self._parse_decimal(row[qty_idx] if qty_idx is not None else '1')
                    unit_price = self._parse_decimal(row[price_idx] if price_idx is not None else '0')
                    line_total = self._parse_decimal(row[total_idx] if total_idx is not None else str(quantity * unit_price))
                    
                    if description and quantity and unit_price:
                        line_items.append(LineItem(
                            description=str(description).strip(),
                            quantity=quantity,
                            unit_price=unit_price,
                            line_total=line_total
                        ))
                except Exception:
                    continue
        
        return line_items

    def _find_column_index(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords."""
        for i, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header:
                    return i
        return None

    def _parse_decimal(self, value: str) -> Decimal:
        """Parse string to Decimal."""
        if not value:
            return Decimal('0')
        # Clean numeric string
        cleaned = re.sub(r'[^\d.-]', '', str(value))
        try:
            return Decimal(cleaned) if cleaned else Decimal('0')
        except (InvalidOperation, ValueError):
            return Decimal('0')
```

### 4. invoice_qc/validator.py

```python
"""Validation module for invoice data quality control."""
from typing import List, Dict
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

from .models import Invoice, ValidationResult, ValidationError, ValidationSummary


class InvoiceValidator:
    """Validates invoice data against business rules."""
    
    VALID_CURRENCIES = ['EUR', 'USD', 'GBP', 'INR', 'JPY', 'CHF', 'CAD', 'AUD']
    
    def validate_invoices(self, invoices: List[Invoice]) -> ValidationSummary:
        """Validate a list of invoices and return summary."""
        results = []
        seen_invoices = set()
        error_counts = defaultdict(int)
        
        for invoice in invoices:
            errors = []
            
            # Completeness rules
            errors.extend(self._check_completeness(invoice))
            
            # Format rules
            errors.extend(self._check_formats(invoice))
            
            # Business rules
            errors.extend(self._check_business_rules(invoice))
            
            # Anomaly rules
            errors.extend(self._check_anomalies(invoice, seen_invoices))
            
            # Create result
            invoice_id = invoice.invoice_number or invoice.source_file or "UNKNOWN"
            is_valid = len(errors) == 0
            
            result = ValidationResult(
                invoice_id=invoice_id,
                is_valid=is_valid,
                errors=errors
            )
            results.append(result)
            
            # Count errors
            for error in errors:
                error_counts[error.rule] += 1
        
        # Create summary
        valid_count = sum(1 for r in results if r.is_valid)
        
        return ValidationSummary(
            total_invoices=len(invoices),
            valid_invoices=valid_count,
            invalid_invoices=len(invoices) - valid_count,
            error_counts=dict(error_counts),
            validation_results=results
        )

    def _check_completeness(self, invoice: Invoice) -> List[ValidationError]:
        """Check completeness rules."""
        errors = []
        
        # Rule 1: Required fields
        required_fields = {
            'invoice_number': 'Invoice number',
            'invoice_date': 'Invoice date',
            'seller_name': 'Seller name',
            'buyer_name': 'Buyer name'
        }
        
        for field, label in required_fields.items():
            value = getattr(invoice, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(ValidationError(
                    rule="missing_required_field",
                    message=f"{label} is missing or empty"
                ))
        
        # Rule 2: Required amounts
        if invoice.net_total is None:
            errors.append(ValidationError(
                rule="missing_net_total",
                message="Net total is missing"
            ))
        
        if invoice.gross_total is None:
            errors.append(ValidationError(
                rule="missing_gross_total",
                message="Gross total is missing"
            ))
        
        # Rule 3: Currency presence
        if not invoice.currency:
            errors.append(ValidationError(
                rule="missing_currency",
                message="Currency is not specified"
            ))
        
        return errors

    def _check_formats(self, invoice: Invoice) -> List[ValidationError]:
        """Check format rules."""
        errors = []
        
        # Rule 1: Date format
        for date_field in ['invoice_date', 'due_date']:
            date_value = getattr(invoice, date_field, None)
            if date_value:
                try:
                    datetime.strptime(date_value, '%Y-%m-%d')
                except ValueError:
                    errors.append(ValidationError(
                        rule="invalid_date_format",
                        message=f"{date_field} has invalid format (expected YYYY-MM-DD)"
                    ))
        
        # Rule 2: Currency validation
        if invoice.currency and invoice.currency not in self.VALID_CURRENCIES:
            errors.append(ValidationError(
                rule="invalid_currency",
                message=f"Currency '{invoice.currency}' is not in valid set: {self.VALID_CURRENCIES}"
            ))
        
        # Rule 3: Numeric values
        for field in ['net_total', 'tax_amount', 'gross_total', 'tax_rate']:
            value = getattr(invoice, field, None)
            if value is not None:
                try:
                    Decimal(str(value))
                except Exception:
                    errors.append(ValidationError(
                        rule="invalid_numeric_value",
                        message=f"{field} is not a valid number"
                    ))
        
        return errors

    def _check_business_rules(self, invoice: Invoice) -> List[ValidationError]:
        """Check business rules."""
        errors = []
        
        # Rule 1: Date logic
        if invoice.invoice_date and invoice.due_date:
            try:
                inv_date = datetime.strptime(invoice.invoice_date, '%Y-%m-%d')
                due = datetime.strptime(invoice.due_date, '%Y-%m-%d')
                if due < inv_date:
                    errors.append(ValidationError(
                        rule="invalid_date_sequence",
                        message="Due date must be on or after invoice date"
                    ))
            except ValueError:
                pass  # Format errors caught elsewhere
        
        # Rule 2: Total calculation
        if all([invoice.net_total is not None, invoice.tax_amount is not None, invoice.gross_total is not None]):
            calculated_total = invoice.net_total + invoice.tax_amount
            tolerance = invoice.gross_total * Decimal('0.005')  # 0.5% tolerance
            
            if abs(calculated_total - invoice.gross_total) > tolerance:
                errors.append(ValidationError(
                    rule="totals_mismatch",
                    message=f"Net + Tax ({calculated_total}) does not equal Gross total ({invoice.gross_total})"
                ))
        
        # Rule 3: Line item sum
        if invoice.line_items and invoice.net_total is not None:
            line_items_sum = sum(item.line_total for item in invoice.line_items)
            tolerance = invoice.net_total * Decimal('0.01')  # 1% tolerance
            
            if abs(line_items_sum - invoice.net_total) > tolerance:
                errors.append(ValidationError(
                    rule="line_items_sum_mismatch",
                    message=f"Sum of line items ({line_items_sum}) does not match net total ({invoice.net_total})"
                ))
        
        # Rule 4: Tax rate consistency
        if all([invoice.tax_rate is not None, invoice.net_total is not None, invoice.tax_amount is not None]):
            calculated_tax = invoice.net_total * (invoice.tax_rate / Decimal('100'))
            tolerance = invoice.tax_amount * Decimal('0.01')  # 1% tolerance
            
            if abs(calculated_tax - invoice.tax_amount) > tolerance:
                errors.append(ValidationError(
                    rule="tax_calculation_mismatch",
                    message=f"Tax amount ({invoice.tax_amount}) inconsistent with rate {invoice.tax_rate}%"
                ))
        
        return errors

    def _check_anomalies(self, invoice: Invoice, seen_invoices: set) -> List[ValidationError]:
        """Check for anomalies and duplicates."""
        errors = []
        
        # Rule 1: Duplicate detection
        if invoice.invoice_number and invoice.seller_name and invoice.invoice_date:
            invoice_key = (invoice.invoice_number, invoice.seller_name, invoice.invoice_date)
            if invoice_key in seen_invoices:
                errors.append(ValidationError(
                    rule="duplicate_invoice",
                    message=f"Duplicate invoice detected: {invoice.invoice_number}"
                ))
            else:
                seen_invoices.add(invoice_key)
        
        # Rule 2: Negative values
        for field in ['net_total', 'tax_amount', 'gross_total']:
            value = getattr(invoice, field, None)
            if value is not None and value < 0:
                errors.append(ValidationError(
                    rule="negative_amount",
                    message=f"{field} cannot be negative ({value})"
                ))
        
        return errors
```

---

## 🔧 Next Steps

I've created:
1. ✅ Complete project structure
2. ✅ Schema design with 16 fields
3. ✅ 13 validation rules across all categories
4. ✅ Full extractor.py with PDF parsing
5. ✅ Full validator.py with all rules
6. ✅ Data models using Pydantic

**Still to create:**
- CLI interface (cli.py)
- FastAPI application (api/main.py)
- Frontend React application (bonus)
- README.md with full documentation
- Tests and AI usage notes

Would you like me to continue with the remaining files (CLI, API, Frontend, and README)?