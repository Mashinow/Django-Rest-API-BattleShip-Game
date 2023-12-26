import random

from constants import GAME_RULE, LOBBY_GEOMETRY
from battleship_button import BattleshipButton
from movable_ship import MovableShip
from PyQt5.QtCore import QSize

from objects import GlobalObjects


class LobbyManager:
    def __init__(self, obj: GlobalObjects):
        self.gObj = obj
        self.dynamicShips = []
        self.battleshipButtons = []
        self.form = obj.qtObj
        self.create_game_buttons()

    def __del__(self):
        for ship in self.dynamicShips:
            ship.setParent(None)
            ship.deleteLater()
        for button in self.battleshipButtons:
            button.setParent(None)
            button.deleteLater()

    def randomize_labels(self):
        for label in self.dynamicShips:
            if random.randint(0, 1):
                label.labelRotate()
            while True:
                xMax = LOBBY_GEOMETRY.endX - (((label.shipSize - 1) * LOBBY_GEOMETRY.fieldSize) if not label.isVertical else 0)
                yMax = LOBBY_GEOMETRY.endY - (((label.shipSize - 1) * LOBBY_GEOMETRY.fieldSize) if label.isVertical else 0)
                new_x = random.randint(LOBBY_GEOMETRY.startX, xMax)
                new_y = random.randint(LOBBY_GEOMETRY.startY, yMax)
                label.move(new_x, new_y)
                if label.trySetPos():
                    break

    def try_confirm_ships(self):
        for ship in self.dynamicShips:
            if ship.shipSize != len(ship.sells):
                self.gObj.send_log_msg('Не все корабли расположены корректно')
                return
        shipsDict = {1: [], 2: [], 3: [], 4: [], 'GameMode': self.gObj.getGameMode()}
        for ship in self.dynamicShips:
            shipFields = []
            for field in ship.sells:
                field.set_has_ship()
                shipFields.append(field.row + field.col * 10)
            shipsDict[ship.shipSize].append(shipFields)
            ship.setParent(None)
            ship.deleteLater()
            self.dynamicShips = []
        return shipsDict

    def create_game_buttons(self):
        def lobby_buttons():
            startPos = [LOBBY_GEOMETRY.startX, LOBBY_GEOMETRY.startY]
            elemSize = [LOBBY_GEOMETRY.fieldSize, LOBBY_GEOMETRY.fieldSize]
            offs = 0
            for i in range(GAME_RULE.fieldCountX):
                for j in range(GAME_RULE.fieldCountY):
                    new_button = BattleshipButton(i, j, self.form.tabLobby, self.gObj)
                    posX = startPos[0] + ((elemSize[0] + offs) * i)
                    posY = startPos[1] + ((elemSize[1] + offs) * j)
                    new_button.setGeometry(posX, posY, *elemSize)
                    self.battleshipButtons.append(new_button)
                    # if random.randint(1, 4) == 3:
                    #     new_button.set_has_ship()

        def add_ships_with_size(size, count, x, y, step):
            for i in range(count):
                self.dynamicShips.append(MovableShip('', self.form.tabLobby, QSize(size, 40), [x + i * step, y]))

        def movable_ships():
            xStep = LOBBY_GEOMETRY.fieldSize
            yStep = 190
            add_ships_with_size(40, 4, 70, yStep, xStep)
            add_ships_with_size(90, 3, 20, yStep + LOBBY_GEOMETRY.fieldSize, xStep + LOBBY_GEOMETRY.fieldSize)
            add_ships_with_size(140, 2, 20, yStep + (LOBBY_GEOMETRY.fieldSize * 2), xStep + (LOBBY_GEOMETRY.fieldSize * 2))
            add_ships_with_size(190, 1, 70, 340, 0)

        lobby_buttons()
        movable_ships()

