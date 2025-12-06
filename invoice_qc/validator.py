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
