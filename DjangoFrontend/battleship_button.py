from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton
from objects import GlobalObjects


class BattleshipButton(QPushButton):
    def __init__(self, row, col, parent, obj: GlobalObjects, isMyField=True):
        super(BattleshipButton, self).__init__(parent)
        self.gObj = obj
        self.row = row  # Номер строки кнопки
        self.col = col  # Номер столбца кнопки
        self.attacked = False  # Флаг, указывающий, была ли кнопка атакована
        self.has_ship = False  # Флаг, указывающий, находится ли на кнопке часть корабля
        self.isMyField = isMyField
        self.update_color()
        self.clicked.connect(self.handle_click)

        font = QFont()
        font.setPointSize(16)
        self.setFont(font)

    def sendTurnData(self):
        curDict = 'ABCDEFGHIJ'
        ctx = self.gObj.gmCtx
        ctx.turnNum += 1
        curTurn = ctx.turnNum
        curPlayer = ctx.enemyName if self.isMyField else ctx.name
        result = 'попал' if self.has_ship else 'мимо'
        self.gObj.send_log_msg(f'Ход {curTurn}: {curPlayer} атаковал {curDict[self.row]}{self.col} результат {result}')
        if self.has_ship:
            return True

    def attack_process(self):
        self.attacked = True
        self.update_color()
        self.sendTurnData()

    def handle_click(self):
        if not self.gObj.is_your_turn() or self.isMyField or self.attacked:
            return
        self.gObj.gameManager.buttonAttackProcess(self.row + self.col * 10)
        # result = self.attack_process()

    def set_has_ship(self, has_ship=True):
        self.has_ship = has_ship
        if has_ship:
            self.setText("●")

    def update_color(self):
        if self.attacked:
            if self.has_ship:
                background_color = "background-color: rgb(255, 102, 102);"  # Теплый красный цвет при попадании
                self.setText("☠")
            else:
                background_color = "background-color: rgb(102, 102, 255);"  # Теплый синий цвет при промахе
        else:
            background_color = "background-color: rgb(102, 255, 102);"

        # Установка стиля фона кнопки
        self.setStyleSheet(background_color + 'color: grey;')
