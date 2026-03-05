"""functions for preparing and running the main event loop"""

import asyncio
from collections.abc import Callable, Coroutine

tasks: list[Callable[[], Coroutine]] = []


def add_task(task: Callable[[], Coroutine]) -> None:
    """add an async function to be run as a task"""
    tasks.append(task)


def run() -> None:
    """start all defined runnables in an event loop"""

    async def _run() -> None:
        async with asyncio.TaskGroup() as group:
            for task in tasks:
                group.create_task(task())

    asyncio.run(_run())
