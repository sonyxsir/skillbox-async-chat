"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                logins = []
                for client in self.server.clients:
                    logins.append(client.login)
                login = decoded.replace("login:", "").replace("\r\n", "")
                if login in logins:
                    self.transport.write(
                        f"Логин {login} занят, попробуйте другой".encode())
                    self.transport.close()
                else:
                    self.login = login
                    history = self.server.send_history()
                    self.transport.write(
                        f"Привет, {self.login}!\n{history}".encode()
                )
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.buffer_update(format_string)

        for client in self.server.clients:
            if (client.login != self.login) and (client.login != None):
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    buffer: list

    def __init__(self):
        self.clients = []
        self.buffer = []

    def buffer_update(self, message: str):
        if len(self.buffer) > 9:
            self.buffer.remove(self.buffer[0])
        self.buffer.append(message)

    def send_history(self):
        return "\n".join(self.buffer)

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
