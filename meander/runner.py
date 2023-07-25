from abc import ABC, abstractmethod
import asyncio


runnables = []


class Runnable(ABC):
    @abstractmethod
    async def start(self):
        return self


def add_runnable(runnable):
    if not isinstance(runnable, Runnable):
        raise AttributeError("{runnable} is not a Runnable")
    runnables.append(runnable)


def get_runnable():
    """return the most recently appended runnable"""
    if len(runnables):
        return runnables[-1]


def run():

    async def _run():
        await asyncio.gather(
            *[await runnable.start() for runnable in runnables]
        )

    asyncio.run(_run())
