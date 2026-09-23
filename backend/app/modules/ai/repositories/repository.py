"""AI module — repository."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AIExecution
from app.shared.base_repository import BaseRepository


class AIExecutionRepository(BaseRepository[AIExecution]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AIExecution, session)
