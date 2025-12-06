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
