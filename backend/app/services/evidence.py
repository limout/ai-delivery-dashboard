from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory


ACTIVE_STATUSES = {"In Progress", "Blocked"}
BLOCKED_STATUSES = {"Blocked"}
MAX_EVIDENCE_ITEMS = 5


class EvidenceService:
    """Build deterministic, human-readable evidence for delivery insights."""

    def build(
        self,
        insights: list[dict[str, Any]],
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        now = now or datetime.now(timezone.utc)

        by_item: dict[str, list[WorkItemHistory]] = {}

        for event in histories:
            by_item.setdefault(event.work_item_id, []).append(event)

        for events in by_item.values():
            events.sort(key=lambda event: event.timestamp)

        active = [
            item
            for item in work_items
            if item.status in ACTIVE_STATUSES
        ]

        blocked = [
            item
            for item in work_items
            if item.status in BLOCKED_STATUSES
        ]

        active_details = [
            self._item_detail(
                item,
                by_item.get(item.id, []),
                now,
            )
            for item in active
        ]

        active_details.sort(
            key=lambda item: item["age_days"],
            reverse=True,
        )

        blocked_details = [
            self._item_detail(
                item,
                by_item.get(item.id, []),
                now,
            )
            for item in blocked
        ]

        blocked_details.sort(
            key=lambda item: item["age_days"],
            reverse=True,
        )

        result = []

        for insight in insights:
            evidence = {
                "evidence_type": "delivery_work_items",
                "wip_count": len(active),
                "blocked_count": len(blocked),
                "wip_items": active_details[:MAX_EVIDENCE_ITEMS],
                "blocked_items": blocked_details[:MAX_EVIDENCE_ITEMS],
            }

            result.append(
                {
                    **insight,
                    "evidence": evidence,
                }
            )

        return result

    @staticmethod
    def _item_detail(
        item: WorkItem,
        history: list[WorkItemHistory],
        now: datetime,
    ) -> dict[str, Any]:
        entered_active_at = None

        for event in history:
            if event.field != "status":
                continue

            if event.to_value in ACTIVE_STATUSES:
                entered_active_at = event.timestamp

            elif event.from_value in ACTIVE_STATUSES:
                entered_active_at = None

        if entered_active_at is None:
            entered_active_at = item.updated_at or item.created_at

        age_days = 0.0

        if entered_active_at is not None:
            timestamp = EvidenceService._aware(entered_active_at)

            age_days = max(
                0.0,
                (
                    EvidenceService._aware(now) - timestamp
                ).total_seconds()
                / 86400,
            )

        return {
            "evidence_type": "work_item_age",
            "source": item.source,
            "id": item.id,
            "title": item.title,
            "status": item.status,
            "assignee": item.assignee,
            "priority": item.priority,
            "age_days": round(age_days, 2),
        }

    @staticmethod
    def _aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)