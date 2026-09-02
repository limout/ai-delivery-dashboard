from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse

from app.connectors.jira.connector import JiraConnector
from app.metrics.engine import MetricEngine
from app.metrics.registry import get_default_registry
from app.services.delivery_metrics import DeliveryMetricsService

app = FastAPI(
    title="AI Delivery Dashboard",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
@app.get("/")
def dashboard():
    return FileResponse("app/static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    registry = get_default_registry()

    return {
        "available_metrics": [
            {
                "name": metric.name,
                "description": metric.description,
                "category": metric.category,
                "required_data": metric.required_data,
            }
            for metric in registry.list_metrics()
        ]
    }

@app.get("/projects/{project}/metrics")
def project_metrics(
    project: str,
    metric_names: list[str] = Query(...),
):
    connector = JiraConnector()
    engine = MetricEngine(get_default_registry())
    service = DeliveryMetricsService(
        connector=connector,
        metric_engine=engine,
    )

    return service.calculate(
        project=project,
        metric_names=metric_names,
    )