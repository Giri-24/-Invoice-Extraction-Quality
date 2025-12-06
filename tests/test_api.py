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


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


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


def test_stats_endpoint():
    """Test stats endpoint."""
    response = client.get("/stats")
    assert response.status_code == 200
    assert "supported_currencies" in response.json()
