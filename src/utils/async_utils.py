import asyncio
from enum import Enum
from typing import Any, List


class UserProcessingStatus(Enum):
    """Статусы обработки пользователей в checkRating"""

    PROCESSED = "processed"
    BLOCKED = "blocked"
    ERROR = "error"
    SKIPPED = "skipped"


async def run_with_semaphore(tasks: List[Any], max_concurrent: int = 10) -> List[Any]:
    """
    Выполняет список задач с ограничением на количество одновременных выполнений.

    Args:
        tasks: Список корутин для выполнения
        max_concurrent: Максимальное количество одновременных задач

    Returns:
        Список результатов выполнения задач
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_process(task: Any) -> Any:
        async with semaphore:
            return await task

    return await asyncio.gather(*[limited_process(task) for task in tasks])
