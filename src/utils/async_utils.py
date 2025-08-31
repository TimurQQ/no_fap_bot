import asyncio
from enum import Enum


class UserProcessingStatus(Enum):
    """Статусы обработки пользователей в checkRating"""
    PROCESSED = "processed"
    BLOCKED = "blocked"
    ERROR = "error"
    SKIPPED = "skipped"


async def run_with_semaphore(tasks, max_concurrent=10):
    """
    Выполняет список задач с ограничением на количество одновременных выполнений.
    
    Args:
        tasks: Список корутин для выполнения
        max_concurrent: Максимальное количество одновременных задач
        
    Returns:
        Список результатов выполнения задач
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_process(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[limited_process(task) for task in tasks])
