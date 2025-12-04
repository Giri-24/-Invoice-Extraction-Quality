# 🚀 Invoice QC Service - Complete Implementation Guide

This guide provides step-by-step instructions to implement and submit your Invoice Extraction & Quality Control Service project.

## 📋 Pre-Submission Checklist

Before you begin, ensure you have:
- [ ] Access to the sample PDFs from SharePoint
- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed (for frontend)
- [ ] Git installed and configured
- [ ] GitHub account ready
- [ ] 48-72 hours available for implementation
- [ ] Screen recording software for demo video

---

## 🎯 Project Timeline (Recommended)

### Day 1 (8-10 hours)
- ✅ **Hours 1-2**: Download PDFs, analyze invoice structures
- ✅ **Hours 3-4**: Design schema and validation rules
- ✅ **Hours 5-7**: Implement extractor.py (PDF parsing)
- ✅ **Hours 8-10**: Implement validator.py (validation logic)

### Day 2 (8-10 hours)
- ✅ **Hours 1-2**: Create models.py and CLI interface
- ✅ **Hours 3-5**: Build FastAPI application
- ✅ **Hours 6-8**: Test everything with sample PDFs
- ✅ **Hours 9-10**: Fix bugs and edge cases

### Day 3 (6-8 hours)
- ✅ **Hours 1-3**: Build React frontend (bonus)
- ✅ **Hours 4-5**: Write comprehensive README
- ✅ **Hours 6-7**: Create demo video
- ✅ **Hour 8**: Final testing and submission

---

## 📦 Step-by-Step Implementation

### Step 1: Download Sample Invoices

1. Visit the SharePoint link provided in assignment
2. Download all PDF files to a local folder
3. Create project directory:

```bash
mkdir invoice-qc-service
cd invoice-qc-service
mkdir pdfs
# Move downloaded PDFs to pdfs/ folder
```

### Step 2: Analyze Invoice Structure

Open 3-5 sample PDFs and note:
- How invoice numbers appear (e.g., "Invoice No: 12345")
- Date formats used (DD/MM/YYYY, MM/DD/YYYY, etc.)
- Where seller/buyer information is located
- How amounts are labeled (Subtotal, VAT, Total, etc.)
- Table structure for line items

**Create a quick analysis document:**

```
Invoice Structure Analysis:
- Invoice Number Format: "Invoice No: INV-XXXX"
- Date Format: DD/MM/YYYY
- Currency: Symbol appears before amounts (€, $)
- Seller Info: Top left, labeled "From:"
- Buyer Info: Top right, labeled "To:"
- Line Items: Table with columns: Description, Qty, Price, Total
- Totals: Bottom right - Subtotal, VAT (19%), Total
```

### Step 3: Setup Project Structure

```bash
# Initialize Git
git init
echo "# Invoice QC Service" > README.md
git add README.md
git commit -m "Initial commit"

# Create project structure
mkdir -p invoice_qc/api
mkdir -p tests
mkdir -p frontend/src
mkdir -p ai-notes
mkdir output

# Create __init__.py files
touch invoice_qc/__init__.py
touch invoice_qc/api/__init__.py
touch tests/__init__.py
```

### Step 4: Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pdfplumber==0.10.3
python-multipart==0.0.6
click==8.1.7
python-dateutil==2.8.2
pytest==7.4.3
httpx==0.25.2
EOF
```

### Step 5: Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (choose based on OS)
source venv/bin/activate        # macOS/Linux
# OR
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Implement Core Modules

Copy the code provided in previous artifacts:

1. **models.py** - Data models
2. **extractor.py** - PDF extraction logic
3. **validator.py** - Validation rules
4. **cli.py** - Command-line interface
5. **api/main.py** - FastAPI application

### Step 7: Test Extraction

```bash
# Test extraction on sample PDFs
python -m invoice_qc.cli extract \
  --pdf-dir ./pdfs \
  --output test_extracted.json

# Verify output
cat test_extracted.json | python -m json.tool | head -50
```

**Expected Output:**
```json
[
  {
    "invoice_number": "INV-001",
    "invoice_date": "2024-01-10",
    "seller_name": "ACME Corp",
    "buyer_name": "Example Ltd",
    "currency": "EUR",
    "net_total": 100.0,
    "tax_amount": 19.0,
    "gross_total": 119.0,
    "line_items": [...]
  }
]
```

### Step 8: Test Validation

```bash
# Test validation
python -m invoice_qc.cli validate \
  --input test_extracted.json \
  --report test_validation.json

# Check report
cat test_validation.json | python -m json.tool
```

### Step 9: Test API

```bash
# Start API server
uvicorn invoice_qc.api.main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/health

curl -X POST http://localhost:8000/validate-json \
  -H "Content-Type: application/json" \
  -d @test_extracted.json

# Visit http://localhost:8000/docs for Swagger UI
```

### Step 10: Build Frontend (Bonus)

```bash
cd frontend

# Create package.json
npm init -y

# Install dependencies
npm install react react-dom lucide-react
npm install -D vite @vitejs/plugin-react tailwindcss postcss autoprefixer

# Initialize Tailwind
npx tailwindcss init -p

# Copy React code from artifact
# Create src/App.jsx, src/main.jsx, index.html

# Start development server
npm run dev
```

### Step 11: Write README.md

Use the comprehensive README template provided. Customize sections:

- Replace `[Your Name]` with your name
- Add your email and GitHub username
- Update the demo video link once recorded
- Add any project-specific notes

### Step 12: Document AI Usage

Create `ai-notes/README.md`:

```markdown
# AI Usage Notes

## Tools Used
1. ChatGPT-4 - Schema design, regex patterns
2. GitHub Copilot - Code completion

## Example: Wrong AI Suggestion

**Prompt**: "Extract invoice number from PDF"

**AI Suggested**:
```python
invoice_no = re.search(r'Invoice No: (\d+)', text).group(1)
```

**Problem**: 
- Crashes if pattern not found (no null check)
- Only matches numeric invoice numbers
- Case-sensitive

**My Solution**:
```python
for pattern in INVOICE_NUMBER_PATTERNS:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
return None
```
```

### Step 13: Create Demo Video

**Recording Checklist:**

1. **Introduction (2 minutes)**
   - Your name and the project
   - High-level overview of what you built
   - Architecture diagram walkthrough

2. **Code Walkthrough (8-10 minutes)**
   - Open `extractor.py` - explain extraction strategy
   - Open `validator.py` - explain key validation rules
   - Open `cli.py` - show CLI commands
   - Open `api/main.py` - show API endpoints
   - (Bonus) Open frontend - show UI components

3. **Live Demo (5-7 minutes)**
   - Show folder with sample PDFs
   - Run CLI extract command, show output
   - Run validation, show report
   - Start API server
   - Make API calls with curl or Postman
   - (Bonus) Demo frontend - upload PDFs, show results

4. **Wrap-up (1-2 minutes)**
   - Mention key challenges
   - What you learned
   - Future improvements

**Recording Tools:**
- **macOS**: QuickTime Player (free)
- **Windows**: OBS Studio (free)
- **Cross-platform**: Loom (free tier)

**Upload:**
1. Upload to Google Drive
2. Set sharing to "Anyone with the link"
3. Add link to README

### Step 14: Create GitHub Repository

```bash
# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
venv/
.env
*.json
*.pdf
node_modules/
dist/
.DS_Store
EOF

# Stage all files
git add .

# Commit
git commit -m "Complete invoice QC service implementation"

# Create GitHub repo (via GitHub website)
# Then push:
git remote add origin https://github.com/yourusername/invoice-qc-service.git
git branch -M main
git push -u origin main
```

### Step 15: Share Repository

1. Go to repository settings
2. Navigate to "Collaborators"
3. Invite:
   - `deeplogicaitech`
   - `csvinay`

---

## 🧪 Testing Your Implementation

### Manual Test Checklist

#### Extraction Tests
- [ ] Extracts invoice numbers correctly
- [ ] Parses dates in correct format (YYYY-MM-DD)
- [ ] Identifies seller and buyer names
- [ ] Extracts all monetary amounts
- [ ] Parses line items from tables
- [ ] Handles missing fields gracefully

#### Validation Tests
- [ ] Flags missing required fields
- [ ] Validates date formats
- [ ] Checks currency codes
- [ ] Detects totals mismatches
- [ ] Identifies duplicate invoices
- [ ] Catches negative amounts

#### CLI Tests
```bash
# Extract
python -m invoice_qc.cli extract --pdf-dir ./pdfs --output out.json
# Should: Create out.json with all invoices

# Validate
python -m invoice_qc.cli validate --input out.json --report report.json
# Should: Print summary, create report.json

# Full run
python -m invoice_qc.cli full-run --pdf-dir ./pdfs --report report.json
# Should: Run end-to-end, show summary
```

#### API Tests
```bash
# Health check
curl http://localhost:8000/health
# Should: Return {"status": "ok"}

# Validate JSON
curl -X POST http://localhost:8000/validate-json \
  -H "Content-Type: application/json" \
  -d '[{"invoice_number": "TEST"}]'
# Should: Return validation summary

# API docs
# Visit http://localhost:8000/docs
# Should: Show Swagger UI
```

#### Frontend Tests (if implemented)
- [ ] Uploads PDFs successfully
- [ ] Displays validation results
- [ ] Shows error messages correctly
- [ ] Filtering works (show invalid only)
- [ ] UI is responsive

---

## 🐛 Common Issues & Solutions

### Issue 1: PDFPlumber Not Extracting Text

**Symptom**: Empty or null values in extracted JSON

**Solution**:
```python
# Check if PDF has text layer
with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    if not text:
        print("PDF is image-based, needs OCR")
```

### Issue 2: Validation Always Fails

**Symptom**: All invoices marked invalid

**Solution**: Check your test data format
```python
# Make sure dates are strings in YYYY-MM-DD format
# Make sure amounts are Decimal or float, not strings
```

### Issue 3: CLI Module Not Found

**Symptom**: `ModuleNotFoundError: No module named 'invoice_qc'`

**Solution**:
```bash
# Run from project root, not from inside invoice_qc/
cd /path/to/invoice-qc-service
python -m invoice_qc.cli --help
```

### Issue 4: API CORS Errors in Frontend

**Symptom**: Browser console shows CORS errors

**Solution**: Ensure CORS middleware is configured
```python
# In api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 5: Frontend Can't Connect to API

**Symptom**: Network errors in frontend

**Solution**:
```javascript
// Make sure API_BASE matches your API server
const API_BASE = 'http://localhost:8000';

// Or use environment variable
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

---

## 💡 Pro Tips

### Time-Saving Tips

1. **Use AI smartly**: Let AI generate boilerplate, but always review and test
2. **Test incrementally**: Don't wait until everything is done to test
3. **Commit often**: Make small commits as you progress
4. **Document as you go**: Write README sections while fresh in mind

### Code Quality Tips

1. **Type hints**: Use them everywhere for better IDE support
2. **Error handling**: Wrap external calls (PDF reading, API) in try-except
3. **Logging**: Add logging statements for debugging
4. **Constants**: Define magic strings (patterns, currencies) as constants

### Demo Video Tips

1. **Rehearse**: Do a practice run before recording
2. **Script it**: Write bullet points of what to cover
3. **Zoom in**: Make sure code is readable
4. **Speak clearly**: Explain your reasoning, not just what code does
5. **Show personality**: Be enthusiastic, this is your work!

---

## 📊 Evaluation Criteria

Based on the assignment, you'll be evaluated on:

### Technical Implementation (40%)
- Correctness of extraction logic
- Completeness of validation rules
- Code quality and structure
- Error handling

### System Design (25%)
- Schema design choices
- Architecture decisions
- Integration potential
- Scalability considerations

### Documentation (20%)
- README completeness
- Code comments
- AI usage notes
- Design rationale

### Bonus (15%)
- Frontend implementation
- Additional features
- Testing coverage
- Deployment config

---

## 🎓 Learning Outcomes

By completing this project, you'll demonstrate:

- **Data Engineering**: PDF parsing, text extraction, data cleaning
- **Backend Development**: Python, FastAPI, REST APIs
- **Data Validation**: Rule engines, business logic
- **Full-Stack Skills**: React, API integration (bonus)
- **System Design**: Architecture, integration patterns
- **Documentation**: Technical writing, clear communication
- **AI Collaboration**: Effective use of AI tools

---

## 📧 Questions?

If you're stuck:

1. **Check this guide**: Re-read the relevant section
2. **Review the code**: Look at the provided implementations
3. **Test incrementally**: Isolate the problem
4. **Search**: Many common issues have solutions online
5. **Document it**: If you can't solve it, explain your approach

---

## ✅ Final Submission Checklist

Before submitting:

- [ ] All code files created and tested
- [ ] CLI commands work for all three modes
- [ ] API endpoints respond correctly
- [ ] Frontend displays results (if implemented)
- [ ] README.md is complete with all sections
- [ ] AI usage documented with examples
- [ ] Demo video recorded and uploaded
- [ ] GitHub repository created
- [ ] Repository shared with deeplogicaitech and csvinay
- [ ] Video link added to README (public access)
- [ ] All files committed and pushed
- [ ] Tested git clone in fresh directory

---

## 🎉 You're Ready!

You now have everything needed to complete this project successfully. Remember:

- **Focus on core parts first** (A, B, C, D) before bonus
- **Test frequently** to catch issues early
- **Document your thinking** - reviewers want to see your reasoning
- **Have fun!** This is a chance to showcase your skills

Good luck! 🚀

---

**Last Updated**: December 4, 2024