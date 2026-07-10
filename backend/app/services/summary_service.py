"""Summary service — orchestrates DB + LangGraph. Implementation in Phase 2."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession


class SummaryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_summary(self, standup_date: date) -> dict:
        """Load updates, run graph, persist summary. Stub for Phase 1 scaffold."""
        raise NotImplementedError(
            "Summary generation will be implemented in the next phase."
        )
