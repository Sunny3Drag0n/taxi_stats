import asyncio
from taxi_stats.server import Server


if __name__ == "__main__":
    server = Server()
    asyncio.run(server.run())
