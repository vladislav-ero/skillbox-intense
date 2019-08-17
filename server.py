#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#  Modified by Vladislav Eroshenko
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    factory: 'Server'

    ip: str
    login: str = None


    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host
        self.factory.clients.append(self)

        self.sendLine("Welcome to the chat!\n".encode())  # отправляем сообщение клиенту

        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера

        for previous_message in self.factory.list_of_messages:
            self.sendLine(previous_message.encode())



    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)
        if self.login is not None:
            print(f"Client disconnected: {self.login} {self.ip}")
            self.factory.list_of_clients.remove(self.login)
        else:
            print(f"Client disconnected: {self.ip}")

    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован


        При попытке подключения клиента под логином, который уже есть в чате:
        - отправлять клиенту текст с ошибкой "Логин {login} занят, попробуйте другой"
        - отключать от сервера соединение клиента
        """

        message = line.decode()
        print(message)

        if self.login is None:
            # login:admin
            if message.startswith("login:"):
                self.login = message.replace("login:", "")
                if self.login not in self.factory.list_of_clients:
                    self.factory.list_of_clients.append(self.login)
                    notification = f"New client with login: {self.login}"
                    print(notification)
                    self.factory.notify_all_users(notification)
                else:
                    warning_text = f"Login {self.login} is occupied, try another one"
                    self.sendLine(warning_text.encode())
                    print(warning_text)
                    self.factory.clients.remove(self)
                    print(f"Client disconnected: {self.ip}")
                    self.transport.loseConnection()
        else:
            mes = f"{self.login}: {message}"
            self.factory.notify_all_users(mes)
            print(mes)


class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list
    protocol = Client
    list_of_clients: list
    list_of_messages: list

    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []
        self.list_of_clients = []
        self.list_of_messages = []
        print("Server started - OK")

    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("Start listening ...")

    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        if len(self.list_of_messages) < 10:
            self.list_of_messages.append(message)
        else:
            self.list_of_messages.pop(0)
            self.list_of_messages.append(message)

        data = message.encode()  # закодируем текст в двоичное представление
        for user in self.clients:
            user.sendLine(data)


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
