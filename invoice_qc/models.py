"""Data models for invoice extraction and validation."""
from typing import List, Optional
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
