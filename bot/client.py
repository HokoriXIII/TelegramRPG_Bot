# coding=utf-8
"""
Адаптированный клиент Телетона
"""

import sys
import time

import telethon
# from telethon.tl.functions.messages import ReadHistoryRequest
# from telethon.utils import get_input_peer

from sessions import API_ID, API_HASH


class TelethonClient(telethon.TelegramClient):
    """ Основной клиент для работы с Телеграмом """
    def __init__(self, user, phone):
        # Создаем файл сессии
        super().__init__("sessions/" + user, API_ID, API_HASH)
        self.user = user
        self.phone = phone
        self.user_id = 0

    def connect_with_code(self):
        """ Подключается к Телеграму и запрашивает код """
        # Подключаемся к Телеграму
        self.connect()

        # Если ТГ просит код, вводим его и умираем
        # Если много аккаунтов, запускаем через -l
        if not self.is_user_authorized():
            print('Первый запуск. Запрашиваю код...')
            self.send_code_request(self.phone)

            code_ok = False
            while not code_ok:
                code = input('Введите полученный в Телеграме код: ')
                code_ok = self.sign_in(self.phone, code)

            # Выходим, чтобы запросить код в следующей сессии
            sys.exit("{} код получил, перезапускай.".format(self.user))

        self.user_id = self.get_me().id

    '''
    def read_messages(self, entity, messages):
        """ Отправляет уведомление о прочтении сообщений """
        max_id = max(msg.id for msg in messages)
        return self.invoke(ReadHistoryRequest(peer=get_input_peer(entity), max_id=max_id))
    '''

    def get_message(self, entity, repeat=True):
        """
        Собирает последнее сообщение
        entity: адресат-entity
        repeat: повторяем сбор, пока не получим сообщение от адресата
        Возвращает сообщение и его содержимое
        """
        _, messages, senders = self.get_message_history(entity, 10)

        if repeat:
            for _ in range(15):
                if senders[0].id == entity.id:
                    break

                _, messages, senders = self.get_message_history(entity, 10)
                time.sleep(3)

        # self.read_messages(entity, messages)
        message = messages[0]

        if getattr(message, 'media', None):
            content = '<{}> {}'.format(
                message.media.__class__.__name__,
                getattr(message.media, 'caption', ''))

        elif hasattr(message, 'message'):
            content = message.message

        elif hasattr(message, 'action'):
            content = message.action.encode('utf-8')

        else:
            content = message.__class__.__name__

        return message, content
