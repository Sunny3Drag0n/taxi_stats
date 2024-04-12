import asyncio

class Server:
    def __init__(self, handler) -> None:
        self.handler = handler

    async def handle_client(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f"Received {message} from {addr}")

        await self.handler(message=message)

        writer.close()

    async def run(self, ip : str = '127.0.0.1', port : int = 8888):
        server = await asyncio.start_server(
            self.handle_client, ip, port)

        addr = server.sockets[0].getsockname()
        print(f'Запущен сервер: {addr}:{port}')

        async with server:
            await server.serve_forever()