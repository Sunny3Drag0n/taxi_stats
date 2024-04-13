import asyncio
from taxi_stats.core import Core
from taxi_stats.server import Server


async def start():
    core = Core()
    server = Server(core=core)

    await server.run()
    await core.run_event_loop()


if __name__ == "__main__":
    asyncio.run(start())
