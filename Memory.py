from typing import Callable

from CommandTypes import Command
from MagicNumber import MagicNumber

class CacheLine:
    data: int
    timestamp: int

    def __init__(self, data=0, timestamp=0):
        self.data = data
        self.timestamp = timestamp

class Cache:
    lines: {int: CacheLine}

    def __init__(self):
        self.lines = {}

    def touch(self, line, tick):
        self.lines[line].timestamp = tick

    def find_lru_line(self):
        return min(self.lines, key=lambda addr: self.lines[addr].timestamp)


class Memory:
    memory: {int: Command | int}
    cache: Cache

    def __init__(self):
        self.memory = {}
        self.cache = Cache()

    def read(self, addr: int, tick_callback, now: Callable):
        if addr in self.cache.lines:
            tick_callback(info="CACHE HIT; ")
            self.cache.touch(addr, now())
            return self.cache.lines[addr].data
        if len(self.cache.lines) == MagicNumber.CACHE_LINES_COUNT.value and MagicNumber.CACHE_LINES_COUNT.value != 0:
            victim = self.cache.find_lru_line()
            del self.cache.lines[victim]

        for _ in range(MagicNumber.MEMORY_ACCESS_TIME.value):
            tick_callback(info="CACHE MISS; ")

        value = self.memory.get(addr, 0)
        if MagicNumber.CACHE_LINES_COUNT.value != 0:
            self.cache.lines[addr] = CacheLine(
                data=value,
                timestamp=now()
            )

        return value


    def write(self, addr: int, value: Command | int, tick_callback, now: Callable):
        self.memory[addr] = value

        for _ in range(MagicNumber.MEMORY_ACCESS_TIME.value):
            tick_callback(info="WRITE-THROUGH; ")

        if addr in self.cache.lines:
            self.cache.lines[addr].data = value
            self.cache.touch(addr, now())
            return

        if len(self.cache.lines) == MagicNumber.CACHE_LINES_COUNT.value and MagicNumber.CACHE_LINES_COUNT.value != 0:
            victim = self.cache.find_lru_line()
            del self.cache.lines[victim]

        if MagicNumber.CACHE_LINES_COUNT.value != 0:
            self.cache.lines[addr] = CacheLine(
                data=value,
                timestamp=now()
            )