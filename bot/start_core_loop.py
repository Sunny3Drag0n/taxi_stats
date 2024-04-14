import asyncio
from taxi_stats.core import QueryCore
import logging, sys


async def start():
    core = QueryCore()
    await core.run_event_loop()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )
    asyncio.run(start())
