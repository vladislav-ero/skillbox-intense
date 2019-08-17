#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#  Modified by Vladislav Eroshenko
#
#  Copyright © 2019
#
#  Консольный клиент для подключения к серверу

from twisted.internet import reactor, stdio
from twisted.internet.protocol import Protocol, ClientFactory


class MessageHandler(Protocol):
    """Класс для работы параллельного ввода / вывода"""

    output = None
    # output = input("Your message: ")

    def dataReceived(self, data: bytes):
        """Обработчик нового сообщения от сервера / ввода пользователя"""

        if self.output:
            self.output.write(data)


class User(MessageHandler):
    """Класс для отправки/обработки сообщений сервера"""

    def wrap(self):
        """Обработка ввода / вывода в терминале"""

        handler = MessageHandler()
        handler.output = self.transport

        wrapper = stdio.StandardIO(handler)

        self.output = wrapper

    def connectionMade(self):
        """
        Обработчик успешного соединения

        - посылаем логин на сервер
        - запускаем ввод/вывод
        """
        self.send_message(f"login:{self.factory.login}")
        self.wrap()

    def send_message(self, content: str):
        """Обаботчик отправки сообщения на сервер"""

        content = f"{content}\n"
        self.transport.write(content.encode())


class Connector(ClientFactory):
    """
    Класс для создания подключения к серверу
    """

    protocol = User
    login: str

    def __init__(self, login: str):
        """Создание менеджера подключений (сохраняем логин)"""

        self.login = login

    def startedConnecting(self, connector):
        """Обработчик установки соединения (выводим сообщение)"""

        print("Successful connection")

    def clientConnectionFailed(self, connector, reason):
        """Обработчик неудачного соединения (отключаем reactor)"""

        print("Connection attempt failed")
        reactor.callFromThread(reactor.stop)

    def clientConnectionLost(self, connector, reason):
        """Обработчик отключения соединения (отключаем reactor)"""

        print("Connection was lost")
        reactor.callFromThread(reactor.stop)


if __name__ == '__main__':
    # запрашиваем имя пользователя для подключения
    user_login = input("Your login: ")

    # параметры соединения
    reactor.connectTCP(
        "localhost",
        7410,
        Connector(user_login)
    )

    # запускаем реактор
    reactor.run()
