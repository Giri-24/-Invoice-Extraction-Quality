"""FastAPI application for invoice QC service."""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import tempfile
import shutil
from pathlib import Path

from ..extractor import InvoiceExtractor
from ..validator import InvoiceValidator
from ..models import Invoice, ValidationSummary


app = FastAPI(
    title="Invoice QC Service",
    description="Invoice Extraction & Quality Control API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "Invoice QC Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "validate": "/validate-json",
            "extract_and_validate": "/extract-and-validate-pdfs"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "invoice-qc-service"}


@app.post("/validate-json", response_model=ValidationSummary)
def validate_json(invoices: List[Invoice]):
    """
    Validate a list of invoice JSON objects.
    
    Args:
        invoices: List of invoice objects to validate
        
    Returns:
        ValidationSummary with results and statistics
    """
    try:
        validator = InvoiceValidator()
        summary = validator.validate_invoices(invoices)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    """
    Extract data from PDF files and validate them.
    
    Args:
        files: List of PDF files to process
        
    Returns:
        Dictionary with extracted invoices and validation summary
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Create temporary directory for PDFs
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files
        for upload_file in files:
            if not upload_file.filename.endswith('.pdf'):
                continue
            
            file_path = Path(temp_dir) / upload_file.filename
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(upload_file.file, f)
        
        # Extract invoices
        extractor = InvoiceExtractor()
        invoices = extractor.extract_from_directory(temp_dir)
        
        # Validate
        validator = InvoiceValidator()
        summary = validator.validate_invoices(invoices)
        
        return {
            "extracted_invoices": [inv.model_dump(mode='json') for inv in invoices],
            "validation_summary": summary.model_dump(mode='json')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/stats")
def get_stats():
    """Get service statistics."""
    return {
        "supported_currencies": InvoiceValidator.VALID_CURRENCIES,
        "validation_rules": {
            "completeness": 4,
            "format": 3,
            "business": 4,
            "anomaly": 2
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
