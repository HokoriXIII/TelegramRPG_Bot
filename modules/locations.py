# coding=utf-8
"""
Все локации для игры
"""
import random
import time


from bot.data import WOODS, CAVE, SHORE
from sessions import CAVE_LEVEL, CAVE_CHANCE


class Location(object):
    """ Локация, любое место в игре, куда можем отправиться """
    def __init__(self, console, command, instant, prob):
        """
        console: название в консоли
        command: любое значение, на которое будет ориентироваться .emoji
        instant: требует ли выполнение команды времени
        after: время, через которое поход в локацию будет доступен
        """
        self.console = console
        self.command = command
        self.instant = instant
        self.prob = prob
        self.after = 0

    def postpone(self):
        """ Откладываем поход в локацию """
        seconds = random.random() * 1200 + 900
        self.after = time.time() + seconds
        return seconds / 60

    @property
    def travel(self):
        """ Определяет, идем или не идем в локацию """
        if random.random() < self.prob:
            return True
        return False

    @property
    def emoji(self):
        """ Возвращает команду, по которой осуществляется поход в локацию """
        return self.command

    def update(self, level, available):
        """ Метод обновления для перезаписи """
        pass


class Random(Location):
    """ Локация, в которой ходим по случайной команде """
    @property
    def emoji(self):
        """ Одна из случайных команд """
        return random.choice(self.command)


class Adventures(Location):
    """ Локация для всех приключений """
    def __init__(self, console, command, instant, prob):
        super().__init__(console, command, instant, prob)
        self.level = False
        self.available = []

    @property
    def emoji(self):
        # Побережье перестало быть интересным
        # if SHORE in self.available:
        #     return SHORE

        if CAVE in self.available:
            if self.level >= CAVE_LEVEL and random.random() < CAVE_CHANCE:
                return CAVE

        if WOODS in self.available:
            return WOODS

        return "/inv"

    def update(self, level, available):
        """ Обновляет параметры, от которых зависит выбор локации """
        self.level = level
        self.available = [c for c in self.command if c in available]


RANDOM_COMMANDS = [
    "/top",
    "/worldtop",
    "/hero",
    # "/report",
    # "/inv",
    # "/trades"
]

ADVENTURES = [
    WOODS,
    CAVE,
    SHORE,
    # CARAVANS,
]

LOCATIONS = [
    Location("запрос героя", "🏅Герой", True, 0.7),
    Location("визит в замок", "🏰Замок", True, 0.6),
    Adventures("поход", ADVENTURES, False, 1),
    Random("случайную команду", RANDOM_COMMANDS, True, 0.7),
    # (!) 'arena': Location("поход на арену", "(!)", False),
    # (!) 'build': Location("поход на стройку", "/build_(!)", False),
]
