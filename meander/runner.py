"""functions for preparing and running the main event loop"""
from abc import ABC, abstractmethod
import asyncio


runnables = []


class Runnable(ABC):  # pylint: disable=too-few-public-methods
    """base class for all things added using add_runnable"""

    @abstractmethod
    async def start(self):
        """called right before launching gathering in event loop"""
        return self


def add_runnable(runnable):
    """add/register a new runnable

    only makes sense before calling run"""
    if not isinstance(runnable, Runnable):
        raise AttributeError("{runnable} is not a Runnable")
    runnables.append(runnable)


def run():
    """start all defined runnables in an event loop"""

    async def _run():
        async with asyncio.TaskGroup() as tasks:
            for runnable in runnables:
                tasks.create_task(await runnable.start())

    asyncio.run(_run())
