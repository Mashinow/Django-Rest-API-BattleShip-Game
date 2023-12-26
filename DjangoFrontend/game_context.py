from constants import GAME_MODES


class GameContext:
    def __init__(self):
        self.isYourTurn = False
        self.gameMode = GAME_MODES.singlePlayer
        self.name = ''
        self.enemyName = ''
        self.turnNum = 0
        self.id = 0
