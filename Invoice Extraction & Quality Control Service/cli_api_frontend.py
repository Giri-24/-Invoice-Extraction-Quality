# ============================================================================
# FILE: invoice_qc/cli.py
# ============================================================================
"""Command-line interface for invoice QC operations."""
import json
import click
from pathlib import Path
from typing import Optional

from .extractor import InvoiceExtractor
from .validator import InvoiceValidator
from .models import Invoice


@click.group()
def cli():
    """Invoice Quality Control CLI Tool."""
    pass


@cli.command()
@click.option('--pdf-dir', required=True, help='Directory containing PDF invoices')
@click.option('--output', required=True, help='Output JSON file path')
def extract(pdf_dir: str, output: str):
    """Extract invoice data from PDFs."""
    click.echo(f"📄 Extracting invoices from: {pdf_dir}")
    
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)
    
    # Convert to JSON
    invoices_data = [inv.model_dump(mode='json') for inv in invoices]
    
    # Write output
    with open(output, 'w') as f:
        json.dump(invoices_data, f, indent=2, default=str)
    
    click.echo(f"✅ Extracted {len(invoices)} invoices → {output}")


@cli.command()
@click.option('--input', required=True, help='Input JSON file with extracted invoices')
@click.option('--report', required=True, help='Output validation report JSON')
def validate(input: str, report: str):
    """Validate extracted invoice data."""
    click.echo(f"🔍 Validating invoices from: {input}")
    
    # Load invoices
    with open(input, 'r') as f:
        invoices_data = json.load(f)
    
    invoices = [Invoice(**inv) for inv in invoices_data]
    
    # Validate
    validator = InvoiceValidator()
    summary = validator.validate_invoices(invoices)
    
    # Write report
    with open(report, 'w') as f:
        json.dump(summary.model_dump(mode='json'), f, indent=2)
    
    # Print summary
    click.echo("\n" + "="*50)
    click.echo("📊 VALIDATION SUMMARY")
    click.echo("="*50)
    click.echo(f"Total Invoices:   {summary.total_invoices}")
    click.echo(f"✅ Valid:         {summary.valid_invoices}")
    click.echo(f"❌ Invalid:       {summary.invalid_invoices}")
    
    if summary.error_counts:
        click.echo("\n🔴 Top Errors:")
        for error_type, count in sorted(summary.error_counts.items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
            click.echo(f"  • {error_type}: {count}")
    
    click.echo(f"\n📝 Full report saved to: {report}")
    
    # Exit with error code if there are invalid invoices
    if summary.invalid_invoices > 0:
        raise SystemExit(1)


@cli.command()
@click.option('--pdf-dir', required=True, help='Directory containing PDF invoices')
@click.option('--report', required=True, help='Output validation report JSON')
@click.option('--save-extracted', help='Optionally save extracted JSON')
def full_run(pdf_dir: str, report: str, save_extracted: Optional[str]):
    """Run full pipeline: extract + validate."""
    click.echo("🚀 Starting full pipeline...\n")
    
    # Extract
    click.echo(f"📄 Step 1: Extracting from {pdf_dir}")
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)
    click.echo(f"✅ Extracted {len(invoices)} invoices\n")
    
    # Save extracted if requested
    if save_extracted:
        invoices_data = [inv.model_dump(mode='json') for inv in invoices]
        with open(save_extracted, 'w') as f:
            json.dump(invoices_data, f, indent=2, default=str)
        click.echo(f"💾 Saved extracted data → {save_extracted}\n")
    
    # Validate
    click.echo("🔍 Step 2: Validating invoices")
    validator = InvoiceValidator()
    summary = validator.validate_invoices(invoices)
    
    # Write report
    with open(report, 'w') as f:
        json.dump(summary.model_dump(mode='json'), f, indent=2)
    
    # Print summary
    click.echo("\n" + "="*50)
    click.echo("📊 VALIDATION SUMMARY")
    click.echo("="*50)
    click.echo(f"Total Invoices:   {summary.total_invoices}")
    click.echo(f"✅ Valid:         {summary.valid_invoices}")
    click.echo(f"❌ Invalid:       {summary.invalid_invoices}")
    
    if summary.error_counts:
        click.echo("\n🔴 Top Errors:")
        for error_type, count in sorted(summary.error_counts.items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
            click.echo(f"  • {error_type}: {count}")
    
    click.echo(f"\n📝 Full report saved to: {report}")
    click.echo("="*50 + "\n")
    
    if summary.invalid_invoices > 0:
        raise SystemExit(1)


if __name__ == '__main__':
    cli()


# ============================================================================
# FILE: invoice_qc/api/main.py
# ============================================================================
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