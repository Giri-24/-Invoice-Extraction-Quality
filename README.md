# AI Usage Documentation

This document details the use of AI tools during the development of the Invoice QC Service.

## Tools Used

1. **Claude (Anthropic)** - Primary AI assistant
2. **ChatGPT-4 (OpenAI)** - Secondary consultation
3. **GitHub Copilot** - Code completion

## AI Usage Summary

### 1. Schema Design (Part A)

**Tool**: Claude  
**Prompt**: "Help me design a comprehensive invoice schema with 16+ fields suitable for B2B invoices. Include validation rules."

**AI Output**: Initial schema with 12 fields and basic validation rules.

**What I Changed**:
- Extended to 16 fields based on actual PDF analysis
- Added more specific validation rules (13 total)
- Defined line_items structure with proper Decimal types
- Added tolerance percentages for business rules

**Why**: AI suggestion was too generic; real invoices have more complexity.

---

### 2. Regex Pattern Generation (Part B)

**Tool**: Claude + ChatGPT-4  
**Prompt**: "Generate Python regex patterns to extract invoice numbers that appear as 'Invoice No: 12345', 'INV-12345', 'Invoice #12345', etc."

**AI Suggested**:
```python
pattern = r'Invoice No:\s*(\d+)'
```

**Problem**: 
- Only matches "Invoice No:" exactly (case-sensitive)
- Only captures numeric invoice numbers
- Doesn't handle variations like "Invoice Number", "Invoice #"

**My Solution**:
```python
INVOICE_NUMBER_PATTERNS = [
    r'Invoice\s+(?:Number|No\.?|#)\s*:?\s*([A-Z0-9-]+)',
    r'Invoice\s+([A-Z0-9-]+)',
    r'INV[-#]?\s*([A-Z0-9-]+)',
]
# Added re.IGNORECASE flag
# Changed \d+ to [A-Z0-9-]+ for alphanumeric support
```

**Why**: Real invoices use varied formats; AI patterns were too restrictive.

---

### 3. Date Parsing Logic

**Tool**: Claude  
**Prompt**: "Parse dates from invoices in formats DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY into YYYY-MM-DD"

**AI Suggested**:
```python
from datetime import datetime
date_obj = datetime.strptime(date_str, '%d/%m/%Y')
return date_obj.strftime('%Y-%m-%d')
```

**Problem**: Only handles one format; crashes if format doesn't match.

**My Improvement**:
```python
def _extract_date(self, text: str, patterns: List[str]) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Try multiple formats
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%d.%m.%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
    return None
```

**Why**: Needed fallback logic to handle various date formats gracefully.

---

### 4. FastAPI Endpoint Design

**Tool**: Claude  
**Prompt**: "Create FastAPI endpoint that accepts a list of invoices and returns validation summary"

**AI Generated**:
```python
@app.post("/validate")
def validate(invoices: List[dict]):
    # validation logic
    return {"status": "ok", "results": []}
```

**What I Changed**:
```python
@app.post("/validate-json", response_model=ValidationSummary)
def validate_json(invoices: List[Invoice]):
    try:
        validator = InvoiceValidator()
        summary = validator.validate_invoices(invoices)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
```

**Improvements**:
- Used Pydantic models (`List[Invoice]`) instead of `List[dict]`
- Added `response_model` for automatic OpenAPI documentation
- Implemented proper error handling with HTTPException
- Renamed to `/validate-json` for clarity

**Why**: AI lacked type safety and proper API design practices.

---

### 5. Table Parsing for Line Items

**Tool**: ChatGPT-4  
**Prompt**: "Extract line items from PDF tables using pdfplumber"

**AI Suggested**:
```python
tables = page.extract_tables()
for table in tables:
    for row in table[1:]:  # Skip header
        line_items.append({
            'description': row[0],
            'quantity': row[1],
            'price': row[2]
        })
```

**Problem**:
- Assumes fixed column positions
- No header detection
- Crashes if table structure varies
- No data type conversion

**My Solution**:
```python
def _extract_line_items(self, tables: List[List[List[str]]]) -> List[LineItem]:
    line_items = []
    for table in tables:
        headers = [str(h).lower() if h else '' for h in table[0]]
        
        # Dynamic column detection
        desc_idx = self._find_column_index(headers, ['description', 'item'])
        qty_idx = self._find_column_index(headers, ['quantity', 'qty'])
        price_idx = self._find_column_index(headers, ['price', 'unit price'])
        
        for row in table[1:]:
            try:
                description = row[desc_idx] if desc_idx is not None else row[0]
                quantity = self._parse_decimal(row[qty_idx] if qty_idx is not None else '1')
                unit_price = self._parse_decimal(row[price_idx] if price_idx is not None else '0')
                
                line_items.append(LineItem(...))
            except Exception:
                continue
```

**Why**: Needed flexible header detection and robust error handling.

---

### 6. CLI Design

**Tool**: Claude  
**Prompt**: "Create CLI with click library for extract, validate, and full-run commands"

**AI Output**: Basic structure with commands but minimal user feedback.

**What I Added**:
- Rich console output with emojis (📄, ✅, ❌, 🔍)
- Progress indicators
- Summary statistics in formatted tables
- Exit codes for CI/CD integration
- `--save-extracted` option for debugging

**Why**: AI focused on functionality; I added UX improvements for real-world use.

---

## Key Lessons Learned

### What AI Does Well ✅
1. **Boilerplate code** - FastAPI setup, Pydantic models
2. **Pattern suggestions** - Initial regex patterns
3. **Structure** - Module organization, file layout
4. **Documentation** - Docstring templates

### What AI Struggles With ❌
1. **Domain knowledge** - Understanding invoice variations
2. **Edge cases** - Handling malformed PDFs, missing data
3. **Error handling** - Try-except blocks, graceful degradation
4. **Performance** - Optimization, efficient algorithms
5. **Real-world testing** - Patterns work in theory but fail on actual PDFs

### Best Practices

1. **Always test AI suggestions** on real data
2. **Iterate on AI output** - use it as a starting point
3. **Add error handling** - AI often generates happy-path code
4. **Validate assumptions** - AI makes assumptions about data structure
5. **Document changes** - Track what you modified and why

---

## Example Conversation Snippets

### Conversation 1: Validation Rules

**Me**: "What validation rules should I include for invoice QC?"

**AI**: "Check required fields, validate formats, ensure totals match"

**Me**: "Give me specific rules with tolerance levels"

**AI**: [Provided 8 generic rules]

**My Action**: Extended to 13 rules with specific tolerances (0.5% for totals, 1% for line items)

---

### Conversation 2: PDF Extraction

**Me**: "How do I extract amounts from PDF text like 'Total: €119.00'?"

**AI**: 
```python
amount = re.search(r'Total:\s*(\d+\.\d+)', text).group(1)
```

**Problem**: Crashes if not found; doesn't handle currency symbols

**My Fix**:
```python
patterns = [
    r'Total\s*:?\s*([€$£¥]?[\d,]+\.?\d*)',
    r'Grand\s+Total\s*:?\s*([€$£¥]?[\d,]+\.?\d*)'
]
for pattern in patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        amount_str = re.sub(r'[€$£¥,]', '', match.group(1))
        return Decimal(amount_str)
return None
```

---

## Conclusion

AI was invaluable for:
- Rapid prototyping
- Code structure
- Initial implementations

But required significant human refinement for:
- Production readiness
- Edge case handling
- Domain-specific logic
- Real-world testing

**Estimated AI contribution**: 40% of code volume, 20% of final logic complexity.

**Time saved**: Approximately 8-10 hours on boilerplate and research.

**Time spent refining**: Approximately 6-8 hours fixing and improving AI suggestions.

---
