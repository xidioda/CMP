from fastapi.testclient import TestClient
from cmp.main import app


def test_healthz():
    """Test basic health check endpoint"""
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_detailed_health():
    """Test detailed health check endpoint"""
    client = TestClient(app)
    resp = client.get("/health/detailed")
    assert resp.status_code == 200
    
    data = resp.json()
    assert "timestamp" in data
    assert "uptime" in data
    assert "system" in data
    assert "performance" in data


def test_performance_health():
    """Test performance metrics endpoint"""
    client = TestClient(app)
    resp = client.get("/health/performance")
    assert resp.status_code == 200
    
    data = resp.json()
    assert "performance_metrics" in data
    assert "system_metrics" in data
    assert "uptime" in data


def test_agents_health():
    """Test agents health check endpoint"""
    client = TestClient(app)
    resp = client.get("/health/agents")
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["status"] == "checked"
    assert "agents" in data
    
    # Check that all expected agents are present
    expected_agents = ["accountant", "cfo", "controller", "director"]
    for agent in expected_agents:
        assert agent in data["agents"]
        assert data["agents"][agent]["status"] == "active"
