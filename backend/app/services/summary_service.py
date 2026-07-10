import time
import uuid
from datetime import date

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import graph
from app.agents.preclean import preclean_updates
from app.agents.state import GraphState
from app.core.config import get_settings
from app.core.exceptions import IncompleteUpdatesError, NotFoundError
from app.db.models.member import Member
from app.db.models.summary import Summary, SummaryStatus
from app.db.models.update import Update
from app.schemas.summary import (
    SummaryDetailResponse,
    SummaryResponse,
    StandupSummary,
    render_markdown,
)

logger = structlog.get_logger(__name__)


class SummaryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _load_raw_updates(self, standup_date: date) -> list[dict]:
        members_result = await self.db.execute(
            select(Member).where(Member.is_active.is_(True)).order_by(Member.name)
        )
        members = members_result.scalars().all()
        updates_result = await self.db.execute(
            select(Update).where(Update.standup_date == standup_date)
        )
        updates_by_member = {u.member_id: u for u in updates_result.scalars().all()}

        missing = [
            m.name
            for m in members
            if m.id not in updates_by_member
            or not updates_by_member[m.id].yesterday.strip()
            or not updates_by_member[m.id].today.strip()
        ]
        if missing:
            raise IncompleteUpdatesError(
                "All team members must have yesterday, today, and blockers filled "
                f"before summarizing. Missing or incomplete: {', '.join(missing)}"
            )

        raw_updates = []
        for member in members:
            update = updates_by_member[member.id]
            raw_updates.append(
                {
                    "name": member.name,
                    "yesterday": update.yesterday,
                    "today": update.today,
                    "blockers": update.blockers or "",
                }
            )
        return preclean_updates(raw_updates)

    async def generate_summary(self, standup_date: date | None = None) -> SummaryResponse:
        target_date = standup_date or date.today()
        settings = get_settings()
        raw_updates = await self._load_raw_updates(target_date)

        initial = GraphState(
            standup_date=target_date.isoformat(),
            raw_updates=raw_updates,
        )
        start = time.perf_counter()
        final_dict = await graph.ainvoke(
            initial.model_dump(),
            config={"recursion_limit": settings.GRAPH_RECURSION_LIMIT},
        )
        final = GraphState.model_validate(final_dict)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "graph_complete",
            duration_ms=duration_ms,
            status=final.status,
            revision_count=final.revision_count,
            usage=final.usage,
        )

        if not final.parsed_summary:
            raise IncompleteUpdatesError(
                "Summary generation failed — no parsed summary produced."
            )

        degraded = final.status == "degraded"
        rendered = render_markdown(
            final.parsed_summary, target_date, degraded=degraded
        )
        sanitizer_flags = {}
        if final.sanitized_updates:
            sanitizer_flags = {
                m.name: [f.value for f in m.flags] for m in final.sanitized_updates.members
            }

        total_usage = {"input_tokens": 0, "output_tokens": 0}
        for node_usage in final.usage.values():
            total_usage["input_tokens"] += node_usage.get("input_tokens", 0)
            total_usage["output_tokens"] += node_usage.get("output_tokens", 0)

        model_meta = {
            "models": {
                "sanitizer": settings.SANITIZER_MODEL,
                "planner": settings.PLANNER_MODEL,
                "summarizer": settings.SUMMARIZER_MODEL,
                "validator": settings.VALIDATOR_MODEL,
            },
            "revision_count": final.revision_count,
            "usage": final.usage,
            "usage_total": total_usage,
            "sanitizer_flags": sanitizer_flags,
            "graph_duration_ms": duration_ms,
            "error": final.error,
        }

        summary_row = Summary(
            standup_date=target_date,
            plan=final.plan.model_dump() if final.plan else None,
            content=final.parsed_summary.model_dump(),
            rendered_markdown=rendered,
            status=SummaryStatus.degraded if degraded else SummaryStatus.validated,
            model_meta=model_meta,
            prompt_version="v1",
        )
        self.db.add(summary_row)
        await self.db.flush()
        await self.db.refresh(summary_row)

        return SummaryResponse(
            summary_id=summary_row.id,
            status="degraded" if degraded else "validated",
            content=final.parsed_summary,
            rendered_markdown=rendered,
            model_meta=model_meta,
        )

    async def get_summary(self, summary_id: uuid.UUID) -> SummaryDetailResponse:
        row = await self.db.get(Summary, summary_id)
        if not row:
            raise NotFoundError(f"Summary {summary_id} not found")
        return SummaryDetailResponse(
            id=row.id,
            standup_date=row.standup_date,
            status=row.status.value,
            content=StandupSummary.model_validate(row.content),
            rendered_markdown=row.rendered_markdown,
            model_meta=row.model_meta,
            prompt_version=row.prompt_version,
            created_at=row.created_at,
        )
