from datetime import date, timedelta

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.connectors.azure.connector import AzureDevOpsConnector
from app.connectors.jira.connector import JiraConnector
from app.core.connectors.base import DeliveryConnector
from app.metrics.engine import MetricEngine
from app.metrics.historical import HistoricalMetrics
from app.metrics.registry import get_default_registry
from app.services.delivery_metrics import DeliveryMetricsService
from app.services.evidence import EvidenceService
from app.ai.context import AIContextBuilder
from app.ai.ollama import OllamaProvider
from app.ai.analyzer import AIAnalyzer
from app.services.insight_service import InsightService

app = FastAPI(
    title="AI Delivery Dashboard",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


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


def get_connector(source: str) -> DeliveryConnector:
    normalized = source.lower()

    if normalized == "jira":
        return JiraConnector()

    if normalized in {"azure", "azure_devops"}:
        return AzureDevOpsConnector()

    raise ValueError(f"Unsupported source: {source}")


class CombinedDeliveryConnector(DeliveryConnector):
    """Small adapter that exposes multiple normalized sources as one connector."""

    def __init__(self, connectors: list[DeliveryConnector]):
        self.connectors = connectors
        self._item_sources: dict[str, DeliveryConnector] = {}

    def get_projects(self) -> list[dict]:
        projects = []
        for connector in self.connectors:
            projects.extend(connector.get_projects())
        return projects

    def get_work_items(self, project: str):
        result = []
        self._item_sources = {}

        for connector in self.connectors:
            items = connector.get_work_items(project)
            result.extend(items)
            for item in items:
                self._item_sources[item.id] = connector

        return result

    def get_work_item_history(self, work_item_id: str):
        connector = self._item_sources.get(work_item_id)

        if connector is not None:
            return connector.get_work_item_history(work_item_id)

        # History can also be requested independently of get_work_items().
        # Try each source until one accepts the ID.
        history = []
        for candidate in self.connectors:
            try:
                history = candidate.get_work_item_history(work_item_id)
            except Exception:
                continue
            if history:
                return history

        return []

    def get_iterations(self, project: str) -> list[dict]:
        result = []
        for connector in self.connectors:
            result.extend(connector.get_iterations(project))
        return result

    def get_releases(self, project: str) -> list[dict]:
        result = []
        for connector in self.connectors:
            result.extend(connector.get_releases(project))
        return result


def get_delivery_connector(source: str) -> DeliveryConnector:
    normalized = source.lower()

    if normalized == "all":
        return CombinedDeliveryConnector([
            JiraConnector(),
            AzureDevOpsConnector(),
        ])

    return get_connector(normalized)


@app.get("/sources")
def sources():
    result = []

    for source_name, label in (("jira", "Jira"), ("azure_devops", "Azure DevOps")):
        try:
            connector = get_connector(source_name)
            projects = connector.get_projects()
            result.append({
                "source": source_name,
                "label": label,
                "status": "connected",
                "project_count": len(projects),
            })
        except Exception as exc:
            result.append({
                "source": source_name,
                "label": label,
                "status": "error",
                "project_count": 0,
                "message": str(exc),
            })

    return {"sources": result}


@app.get("/sources/{source}/projects")
def source_projects(source: str):
    connector = get_connector(source)
    projects = connector.get_projects()
    return {"source": source, "projects": projects}


@app.get("/projects/{project}/sources")
def project_sources(project: str):
    sources = []

    for source_name, label in (
        ("jira", "Jira"),
        ("azure_devops", "Azure DevOps"),
    ):
        try:
            connector = get_connector(source_name)
            items = connector.get_work_items(project)
            sources.append({
                "source": source_name,
                "label": label,
                "status": "connected",
                "item_count": len(items),
            })
        except Exception as exc:
            sources.append({
                "source": source_name,
                "label": label,
                "status": "error",
                "item_count": 0,
                "message": str(exc),
            })

    return {"project": project, "sources": sources}


@app.get("/projects/{project}/work-items")
def project_work_items(
    project: str,
    source: str = "all",
):
    connector = get_delivery_connector(source)
    items = connector.get_work_items(project)

    return {
        "project": project,
        "source": source,
        "count": len(items),
        "work_items": [item.model_dump(mode="json") for item in items],
    }


@app.get("/projects/{project}/metrics")
def project_metrics(
    project: str,
    metric_names: list[str] = Query(...),
    source: str = "jira",
):
    connector = get_delivery_connector(source)
    engine = MetricEngine(get_default_registry())

    service = DeliveryMetricsService(
        connector=connector,
        metric_engine=engine,
    )

    return service.calculate(
        project=project,
        metric_names=metric_names,
    )


@app.get("/projects/{project}/metrics/history")
def project_metrics_history(
    project: str,
    metric: str = "wip",
    days: int = 14,
    source: str = "jira",
):
    connector = get_delivery_connector(source)

    work_items = connector.get_work_items(project)

    history = []

    for item in work_items:
        history.extend(
            connector.get_work_item_history(item.id)
        )

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    historical = HistoricalMetrics()

    return historical.calculate(
        metric=metric,
        work_items=work_items,
        histories=history,
        start_date=start_date,
        end_date=end_date,
    )

@app.get("/projects/{project}/insights")
def project_insights(
    project: str,
    source: str = "jira",
    days: int = 14,
):
    connector = get_delivery_connector(source)
    engine = MetricEngine(get_default_registry())

    service = InsightService(
        connector=connector,
        metric_engine=engine,
    )

    result = service.analyze(
        project=project,
        days=days,
    )

    work_items = connector.get_work_items(project)
    history = []
    for item in work_items:
        history.extend(connector.get_work_item_history(item.id))

    result["insights"] = EvidenceService().build(
        insights=result.get("insights", []),
        work_items=work_items,
        histories=history,
    )
    result["source"] = source
    return result

@app.get("/projects/{project}/ai/context")
def project_ai_context(
    project: str,
    source: str = "jira",
    days: int = 14,
):
    """Return deterministic delivery context prepared for an AI model.

    The endpoint deliberately reuses the existing insights pipeline and does
    not call an LLM. AIContextBuilder only packages already-derived facts.
    """
    analysis = project_insights(
        project=project,
        source=source,
        days=days,
    )

    context = AIContextBuilder().build(
        analysis=analysis,
        source=source,
    )

    return context.model_dump(mode="json")



@app.get("/projects/{project}/ai/analyze")
def project_ai_analyze(
    project: str,
    source: str = "jira",
    days: int = 14,
):
    """Analyze deterministic delivery context with the configured AI provider."""
    analysis = project_insights(
        project=project,
        source=source,
        days=days,
    )

    context = AIContextBuilder().build(
        analysis=analysis,
        source=source,
    )

    return AIAnalyzer(provider=OllamaProvider()).analyze(context)
