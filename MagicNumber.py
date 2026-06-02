from enum import Enum


class MagicNumber(Enum):
    WORD_LEN = 32
    ADDR_LEN = 20
    ADDR_POS = 20
    OP_CODE_POS = 24

    CACHE_LINES_COUNT = 4
    MEMORY_ACCESS_TIME = 10

    PS_LEN = 6

    START_IP = 2048
