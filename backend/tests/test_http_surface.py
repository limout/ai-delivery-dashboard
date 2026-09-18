import pytest
from fastapi.testclient import TestClient

from app.main import _spa_dist_dir, app


EXPECTED_API_PATHS = {
    "/",
    "/health",
    "/metrics",
    "/sources",
    "/sources/{source}/projects",
    "/projects/{project}/sources",
    "/projects/{project}/work-items",
    "/projects/{project}/metrics",
    "/projects/{project}/metrics/history",
    "/projects/{project}/insights",
    "/projects/{project}/ai/context",
    "/projects/{project}/ai/analyze",
}

SPA_ACCEPT = {"Accept": "text/html"}


def test_react_dashboard_served_at_root():
    if not (_spa_dist_dir() / "index.html").is_file():
        pytest.skip("frontend dist is not built")

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="root"' in response.text
    assert "Classic UI" not in response.text


def test_health_endpoint_unchanged():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_catalog_contract_unchanged():
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
    names = {metric["name"] for metric in response.json()["available_metrics"]}
    assert names == {
        "wip",
        "throughput",
        "cycle_time",
        "lead_time",
        "velocity",
        "commitment_vs_completed",
    }


def test_metrics_html_navigation_serves_spa_when_built():
    if not (_spa_dist_dir() / "index.html").is_file():
        pytest.skip("frontend dist is not built")

    client = TestClient(app)
    response = client.get("/metrics", headers=SPA_ACCEPT)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="root"' in response.text


def test_react_client_routes_serve_spa_when_built():
    if not (_spa_dist_dir() / "index.html").is_file():
        pytest.skip("frontend dist is not built")

    client = TestClient(app)
    for path in ("/work-items", "/insights", "/ai-analysis"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert 'id="root"' in response.text


def test_legacy_app_prefix_redirects_to_root():
    client = TestClient(app, follow_redirects=False)
    response = client.get("/app/?client=AMDARIS")

    assert response.status_code == 307
    location = response.headers["location"]
    assert "/?client=AMDARIS" in location


def test_existing_api_paths_were_not_removed():
    paths = set(app.openapi()["paths"])
    assert EXPECTED_API_PATHS <= paths
