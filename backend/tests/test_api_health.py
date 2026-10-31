"""Integration test for API health and root endpoints."""

from app.models import Category

def test_root_endpoint(client):
    """Test root endpoint returns system information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "Campus Grievance Addressal System" in data["system"]

def test_health_check_endpoint(client, db_session):
    """Test health check returns database status and active category count."""
    # Seed 2 categories in the test session
    cat1 = Category(name="Cat 1")
    cat2 = Category(name="Cat 2")
    db_session.add_all([cat1, cat2])
    db_session.commit()

    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["active_categories"] == 2
