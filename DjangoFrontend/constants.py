from enum import IntEnum
from strenum import StrEnum


class TAB_NAMES(IntEnum):
    login = 0
    main = 1
    lobby = 2
    game = 3
    history = 4


class GAME_MODES(IntEnum):
    singlePlayer = 0
    multiPlayer = 1


class TIMER_NAMES(StrEnum):
    botTurn = 'timerBotTurn'
    waitPlayer = 'timerWaitingPlayer'
    waitMyTurn = 'timerWaitMyTurn'


class GAME_RULE(IntEnum):
    fieldCountX = 10
    fieldCountY = 10


class LOBBY_GEOMETRY(IntEnum):
    startX = 400
    endX = 900
    startY = 100
    endY = 600
    fieldSize = 50

