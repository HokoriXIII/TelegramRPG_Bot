# coding=utf-8

from sessions import SUPERGROUP_ID


# Обязательно проверяем, что в топ-10 есть все эти диалоги
IMPORTANT = {
    777000: "telegram",         # Telegram
    265204902: "cw",            # Бот игры
    278525885: "trade_bot",     # Бот торговли
    313998026: "captcha_bot",   # Бот капчи
    389922706: "penguin",       # Бот Пингвин для склада
    SUPERGROUP_ID: "group",     # Супергруппа, куда будем писать о боях
}

WAR = {
    "Красный": "🇮🇲",
    "Черный": "🇬🇵",
    "Белый": "🇨🇾",
    "Желтый": "🇻🇦",
    "Синий": "🇪🇺",
    "Мятный": "🇲🇴",
    "Сумеречный": "🇰🇮",
    "Лесной форт": "🌲Лесной форт",
    "Горный форт": "⛰Горный форт"
}

WAR_COMMANDS = {
    "к": "Красный",
    "ч": "Черный",
    "б": "Белый",
    "ж": "Желтый",
    "с": "Синий",
    "м": "Мятный",
    "у": "Сумеречный",
    "л": "Лесной форт",
    "г": "Горный форт",
}

# FALL_BACK = "!!"  # забываем приказ

COMMANDS = [
    "/top",
    "/worldtop",
    "/hero",
    # "/report",
    # "/inv",
    # "/trades"
]

DEFEND = "🛡 Защита"
ATTACK = "⚔ Атака"


class Location(object):
    def __init__(self, name, console):
        self.name = name
        self.console = console
        self.after = 0


HERO = "🏅Герой"
CASTLE = "🏰Замок"
WOODS = "🌲Лес"
CAVE = "🕸Пещера"

# У ChatWarsFarmBot должен быть вызываемый без аргументов метод location.name
LOCATIONS = [
    Location('hero', "запрос героя"),
    Location('castle', "визит в замок"),
    Location('farm', "поход фармить"),
    Location('commands', "случайную команду"),
    # Location('worldtop', "запрос рейтинга по замкам"),
    # Location('inv', "проверку инвентаря"),
    # Location('arena', "поход на арену"),
]

COOLDOWN = 7200  # Минимальное время между усталостью

CARAVAN = "/go"
FIGHT = "/fight"

LEVEL_UP = "/level_up"
PLUS_ONE = "+1 ⚔Атака"  # Прокачиваем атаку каждый уровень

INV_EQUIP = "🏷Снаряжение"
INV_CRAFT = "⚒Крафт"

EQUIP_ITEM = "/on_{}"
