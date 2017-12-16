# coding=utf-8
"""
Адаптированный клиент Телетона
"""

import datetime
import os
import random
import sys
import time


from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.helpers import generate_random_long
from telethon.tl.functions.messages.forward_messages import (
    ForwardMessagesRequest)
from telethon.tl.types import UpdateNewMessage, UpdateShort
from telethon.utils import get_input_peer
# from telethon.tl.functions.messages import ReadHistoryRequest
# from telethon.utils import get_input_peer

from bot.data import (
    CHATS, TELEGRAM, GAME, TRADE, CAPTCHA, ENOT,
    PLUS_ONE, LEVEL_UP, ATTACK, DEFEND, HERO,
    SHORE, WAR, WAR_COMMANDS, EQUIP_ITEM,
    COOLDOWN, MONSTER_COOLDOWN, REGROUP
)
from bot.helpers import (
    count_help, get_equipment, get_fight_command, get_flag, get_level, go_wasteland
)
from bot.locations import LOCATIONS
from bot.logger import Logger
from sessions import API_ID, API_HASH, SUPERGROUP


class FarmBot(TelegramClient):
    """ Объект бота для каждой сессии """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    # todo: remove branches and check

    def __init__(self, user, data, silent=True):
        # Если выводим в лог, очищаем его и начинаем с задержкой
        if silent:
            time.sleep(random.random() * 30)
            log_file = 'logs/' + user + '.log'
            with open(log_file, 'w') as target:
                target.truncate()

        else:
            log_file = None

        # Добавляем логгер
        self.logger = Logger(user, log_file, data['girl'])

        # Создаем файл сессии и устанавливаем параметры Телеграма
        # todo: here or later
        super().__init__("sessions/" + user, API_ID, API_HASH)

        # Массив с entity, которые будут использоваться для запросов через Телетон
        self.chats = {}

        # Телефон аккаунта
        self.phone = data['phone']

        # Название сессии для прямых команд боту
        self.user = user

        # self.user_id = 0

        # Состоятние бота
        # 0 — ничего не делаю
        # 1 — занят
        # 2 — жду ветер
        # 3 — выполняю прямую команду
        # 4 — готовлюсь к бою
        # -1 — заблокирован
        self.state = 0

        # Количество раз, которое осталось отправить прямую команду
        self.times = 0

        # Время до следующей передышки
        self.exhaust = time.time()

        # Монстр для сражения — нет гарантии в 100%, что всем монстрам помогут
        self.fight = None

        # Последняя локация
        self.location = 0

        # Все локации
        self.locations = LOCATIONS.copy()
        # Перезаписываем шансы локаций, если они указаны
        if "adventures" in data:
            self.locations[2].command = data["adventures"]

        # Время до следующего дня с походами к монстрам
        self.monster = time.time()

        # Последний приказ из Супергруппы
        self.order = None

        # Основной атрибут для увеличения каждый уровень
        self.primary = PLUS_ONE[ATTACK]
        # Перезаписываем характеристику, если она указана
        if LEVEL_UP in data:
            self.primary = PLUS_ONE[data[LEVEL_UP]]

        # Флаг, уровень и обмундирование определим позднее
        self.equipment = {}
        self.flag = None
        self.level = 0

        # Если запускаем в Виндоуз, переименовываем окно
        if os.name == 'nt':
            os.system("title " + user + " as FarmBot")

        # Поехали!
        self.logger.log("Сеанс {} открыт".format(user))

    def start(self):
        """ Главное древо работы """
        # Подключаемся
        self.connect_with_code()

        # Записываем важные entity
        self.update_chats()

        # Добавляем обработчик входящих событий
        self.add_update_handler(self.update_handler)

        # Определяем изначальные значения
        while not self.equipment and not self.flag and not self.level:
            self.send(self.chats[GAME], "/hero")
            time.sleep(5)
            self.send(self.chats[GAME], "/inv")
            time.sleep(10)

        # Начинаем отправлять команды
        while True:
            # Бой каждые четыре часа. Час перед утренним боем — 8:00 UTC+0
            now = datetime.datetime.utcnow()

            # С 47-й минуты выходим в бой
            if (now.hour) % 4 == 0 and now.minute >= 54:
                if self.state != 4 and self.state != 5:
                    self.battle(DEFEND)

            # Отправляем отчет, но только один раз
            elif (now.hour) % 4 == 1 and now.minute <= 15:
                if self.state != 0:
                    self.state = 0
                    self.send(self.chats[GAME], "/report")
                    self.send(self.chats[SUPERGROUP], self.order)
                    self.order = None

            else:
                if time.time() > self.exhaust:
                    self.send_locations()

            self.logger.sleep(105, "Теперь сплю две минуты", False)

    def connect_with_code(self):
        """ Подключается к Телеграму и запрашивает код """
        # Подключаемся к Телеграму
        connected = self.connect()
        if not connected:
            raise ConnectionError

        # Если Телеграм просит код, вводим его и умираем
        # Каждый отдельный аккаунт запускаем через -l
        if not self.is_user_authorized():
            print('Первый запуск. Запрашиваю код...')
            self.send_code_request(self.phone)

            code_ok = False
            while not code_ok:
                code = input('Введите полученный в Телеграме код: ')

                # Двусторонняя верификация
                try:
                    code_ok = self.sign_in(self.phone, code)

                except RPCError as err:
                    if err.password_required:
                        verified = input(
                            'Введите пароль для двусторонней аутентификации: ')

                        code_ok = self.sign_in(password=verified)

                    else:
                        raise err

            # Выходим, чтобы запросить код в следующем боте
            sys.exit("Код верный! Перезапускай {}.".format(self.user))

    def update_handler(self, tg_updates):
        """ Получает обновления от Телетона и обрабатывает их """
        if self.state == -1:
            return

        if isinstance(tg_updates, UpdateShort):
            return

        for update in tg_updates.updates:
            if isinstance(update, UpdateNewMessage):
                message = update.message

                if message.from_id == TELEGRAM:
                    self.telegram(message)

                elif message.from_id == GAME:
                    self.game(message)

                elif message.from_id == SUPERGROUP:
                    self.group(message)

                elif message.from_id == TRADE or message.from_id == ENOT:
                    pass # todo: read

                elif message.from_id == CAPTCHA:
                    pass # todo: resend


    def telegram(self, message):
        """ Записывает полученный от Телеграма код """
        if "Your login code" in message.message:
            self.logger.log(message.message[:23])

    def game(self, message):
        """ todo: комментарии к блокам и функции """
        text = message.message

        # Сообщения с ветром самые приоритетные
        if "завывает" in text:
            self.state = 2

        # На приключении
        elif "сейчас занят другим приключением" in text:
            self.state = 1

        # Караваны
        elif "/go" in text:
            self.state = 1
            self.send_message(self.chats[GAME], "/go")

        # Устал
        elif "мало единиц выносливости" in text:
            self.logger.log("~Выдохся, поживу без приключений пару часов")
            exhaust = time.time() + COOLDOWN + random.random() * 3600
            self.exhaust = exhaust

        # Оповещаем о потере
        elif "Вы потеряли" in text:
            self.forward(self.chats[GAME], message.id, self.chats[SUPERGROUP])

        # Ответ на /hero
        elif "🏛Твои умения: " in text:
            self.level = get_level(text)
            self.flag = get_flag(text)

        # Ответ на /inv
        elif "Содержимое рюкзака" in text:
            self.equipment = get_equipment(text)

        # Готовимся к атаке конкретной точки
        elif "вояка!" in text:
            self.send(self.chats[GAME], self.order)

        # Готовимся к защите конкретной точки
        elif "защитник!" in text:
            self.send(self.chats[GAME], self.flag)

        # Готовимся к защите
        elif "Ты приготовился" in text:
            if "защите" in text:
                self.equip(DEFEND)
            elif "атаке" in text:
                self.equip(ATTACK)

        # Квесты
        elif "Ты отправился" in text:
            self.state = 1

        # Прямые команды
        elif self.state == 3:
            if "В казне" in text:
                self.state = 0
                self.send(self.chats[SUPERGROUP], "Не из чего строить!")
                return

            self.forward(self.chats[GAME], message.id, self.chats[SUPERGROUP])

            if self.times > 0:
                return

            self.state = 0
            self.send(self.chats[SUPERGROUP], "Все!")

        # Слишком много боев
        elif "Слишком много" in text:
            self.monster = time.time() + MONSTER_COOLDOWN

        # Ответ на квесты
        elif "🌲Лес" in text:
            self.locations[self.location].update(self.level, text)

        # Оповещаем о беде
        elif "питомец в опасности!" in text:
            self.forward(self.chats[SUPERGROUP], message.id, self.chats[SUPERGROUP])

        # Просим ручной выбор класса
        elif "Определись со специализацией" in text:
            self.send(self.chats[SUPERGROUP], "Выберите мне класс!")

        # Запрашиваем повышение уровня
        elif "/level_up" in text:
            self.logger.log("Ух-ты, новый уровень!")
            self.send(self.chats[GAME], "/level_up")

        # Выбираем основную характеристику
        elif "какую характеристику ты" in text:
            self.send(self.chats[GAME], self.primary)
            self.level += 1
            self.send(self.chats[SUPERGROUP], "Новый уровень: `{}`!".format(self.level))

        else:
            self.state = 0

        self.logger.log("Тест: мое состояние == " + str(self.state))
        return

    def group(self, message):
        """ todo """
        parts = message.message.split(": ")

        # Прямая команда должна состоять из двух частей, разделенных двоеточием
        if len(parts) == 2:
            text, times = count_help(parts[0], parts[1],
                                     self.flag, self.level, self.user)

            if text == "/stop":
                self.state = -1
                return

            if text == "/go":
                self.state = 0
                return

            delay = 90
            if "/repair" or "/build" in text:
                delay = 310

            self.state = 3
            self.times = times

            for _ in range(times):
                # Команда подходит, отправляем
                self.send(self.chats[GAME], text)
                self.logger.sleep(delay, "Сон прямого контроля")
                self.times = self.times - 1

            return

        # Игнорируем все, кроме прямых приказов и боев
        text = message.message

        # Кто-то другой взял монстра, перезаписываем
        if text == "+":
            self.fight = None
            return

        # Проверяем, является ли команда приказом развернуться
        if text == REGROUP:
            self.order = None
            self.battle(DEFEND)
            return

        # Приказ выйти в бой
        order = WAR.get(WAR_COMMANDS.get(text.lower()))
        if order:
            self.order = order
            self.battle(ATTACK)
            return

        # Команда сразиться с монстром
        command = get_fight_command(text)
        if not command:
            return

        # Не помогаем на побережье, если не контролируем побережье
        if SHORE in text:
            if self.flag not in text:
                return

        # Не помогаем в Пустошах, если не из Пустошей
        if not go_wasteland(self.flag, text):
            return

        # Не помогаем, если боев на сегодня слишком много
        if time.time() < self.monster and self.state != 0:
            return

        # Устанавливаем монстра
        self.fight = command
        if self.fight:
            self.logger.log("Иду на помощь: {}".format(command))
            self.send(self.chats[GAME], command)
            self.send(self.chats[SUPERGROUP], "+")
            self.fight = ""
        return

    def send_locations(self):
        """ Отправляется во все локации """
        for i, location in enumerate(self.locations):
            self.location = i
            # self.send(self.chats[GAME], "/hero")

            # Пропускаем, если время идти в локацию еще не пришло
            if time.time() - location.after < 0:
                continue

            # Если требует времени, идем как приключение
            if not location.instant:
                self.send(self.chats[GAME], "🗺 Квесты")

            # Пропускаем, если шанс говорит не идти
            if not location.travel:
                self.logger.sleep(10, "Пропускаю " + location.console)
                continue

            # Выбираем, куда пойдем
            emoji = location.emoji

            # Отправляем сообщение с локацией
            self.send(self.chats[GAME], emoji)

            # Откладываем следующий поход
            self.logger.log("Следующий {} через {:.3f} минут".format(
                location.console,
                location.postpone()
            ))

            # Локация не требует затрат времени, пропускаем задержку
            if location.instant:
                self.logger.sleep(5, "Сплю после мгновенной команды")
                continue

            else:
                # self.logger #todo HERE
                self.logger.sleep(5, "Сплю после мгновенной команды")
            # И ради интереса запрашиваем свой профиль
            if random.random() < 0.4:
                self.send(self.chats[GAME], "/hero")

        return

    def battle(self, order):
        """ Переходит в режим атаки или защиты """
        sent = self.send(self.chats[GAME], HERO)
        if not sent:
            return

        time.sleep(2)
        self.state = 4

        sent = self.send(self.chats[GAME], order)
        if not sent:
            return

        time.sleep(2)
        self.equip(order)

    def equip(self, state):
        """
        Надевает указанные предметы
        state: ключ, по которому будут выбраны предметы
        """
        for _, equip in self.equipment.items():
            if len(equip) == 2:
                item = EQUIP_ITEM.format(equip[state])
                self.logger.log("Надеваю: {}".format(item))

                sent = self.send(self.chats[GAME], item)
                if not sent:
                    return

                # todo: time.sleep(random?)

        self.logger.log("Завершаю команду {}".format(state))
        return

    def send(self, entity, text):
        """ Сокращение, потому что бот всегда использует Маркдаун """
        # todo: time.sleep(random?)
        # Не отправляем ничего в оффлайне
        if self.state == -1:
            return False

        # Не отправляем игре в ветер
        if entity == self.chats[GAME] and self.state == 2:
            return False

        self.logger.log("Отправляю " + text)
        self.send_message(entity, text, markdown=True)  # todo: обновить с новым Телетоном
        return True

    def forward(self, from_entity, message_id, to_entity):
        """ Forwards a single message from an entity to entity """
        self.invoke(
            ForwardMessagesRequest(
                get_input_peer(from_entity),
                [message_id],
                [generate_random_long()],
                get_input_peer(to_entity)
            )
        )

    def update_chats(self):
        """ Обновляет список чатов на основе 100 последних диалогов """
        _, entities = self.get_dialogs(100)

        for entity in entities:
            if entity.id in CHATS:
                self.chats[entity.id] = entity

            elif entity.id == SUPERGROUP:
                self.chats[SUPERGROUP] = entity

        return

    def get_message(self, entity, repeat=True):
        """
        Собирает последнее сообщение
        entity: адресат-entity
        repeat: повторяем сбор, пока не получим сообщение от адресата
        Возвращает сообщение и его содержимое
        """
        msgs, sndrs = [], []

        # if read:
        #     for i, sender in enumerate(senders):
        #         if sender.id != self.user_id:
        #             self.send_read_acknowledge(sender, messages[i])

        for _ in range(5):
            if msgs:
                break

            try:
                _, msgs, sndrs = self.get_message_history(entity, 10)

                if repeat:
                    for _ in range(15):
                        if sndrs[0].id == entity.id:
                            break

                        _, msgs, sndrs = self.get_message_history(entity, 10)
                        time.sleep(3)

            except AttributeError:
                time.sleep(5)

        # self.read_messages(entity, msgs)
        message = msgs[0]

        if getattr(message, 'media', None):
            content = '<{}> {}'.format(
                message.media.__class__.__name__,
                getattr(message.media, 'caption', ''))

        elif hasattr(message, 'message'):
            content = message.message

        # (!) разобраться с содержанием сообщения
        elif hasattr(message, 'action'):
            content = ""  # message.action.encode('utf-8')

        else:
            content = message.__class__.__name__

        return message, content
