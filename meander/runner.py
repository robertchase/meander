"""functions for preparing and running the main event loop"""
import asyncio


tasks = []


def add_task(task):
    """add an async function to be run as a task"""
    tasks.append(task)


def run():
    """start all defined runnables in an event loop"""

    async def _run():
        async with asyncio.TaskGroup() as group:
            for task in tasks:
                group.create_task(task())

    asyncio.run(_run())
