import asyncio
from taxi_stats.core import Core
from taxi_stats.server import Server

async def start():
    core = Core()
    server = Server(handler=core._handle)

    asyncio.create_task(core.run_event_loop())
    await server.run()

if __name__ == "__main__":
    asyncio.run(start())