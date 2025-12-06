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
                seller_name="ACME Corp",
                buyer_name="Another Client"
            )
        ]
        
        validator = InvoiceValidator()
        summary = validator.validate_invoices(invoices)
        
        assert summary.invalid_invoices >= 1
    
    def test_negative_amounts(self):
        invoice = Invoice(
            invoice_number="INV-001",
            net_total=Decimal("-100"),
            gross_total=Decimal("119")
        )
        validator = InvoiceValidator()
        seen = set()
        results = validator._check_anomalies(invoice, seen)
        
        assert any("negative" in e.message.lower() for e in results)
