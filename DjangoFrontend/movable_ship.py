from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtCore import Qt, QRect

from battleship_button import BattleshipButton
from constants import LOBBY_GEOMETRY


class MovableShip(QLabel):
    def __init__(self, text, parent, initial_size, pos):
        super(MovableShip, self).__init__(text, parent)
        self.setGeometry(pos[0], pos[1], initial_size.width(), initial_size.height())
        self.setMouseTracking(True)
        self.shipSize = int(max(self.size().width(), self.size().height()) / min(self.size().width(), self.size().height()))
        self.setStyleSheet("QLabel { background-color : lightblue; }")
        self.isVertical = False
        self.sells = []

    def labelRotate(self):
        current_size = self.size()
        self.resize(current_size.height(), current_size.width())
        self.isVertical = not self.isVertical

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.drag_start_position = event.globalPos()
        elif event.buttons() == Qt.RightButton:
            self.labelRotate()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_start_position') and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.drag_start_position
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_start_position = event.globalPos()

    def trySetPos(self):
        self.sells = []
        xMax = LOBBY_GEOMETRY.endX - (((self.shipSize - 1) * LOBBY_GEOMETRY.fieldSize) if not self.isVertical else 0)
        yMax = LOBBY_GEOMETRY.endY - (((self.shipSize - 1) * LOBBY_GEOMETRY.fieldSize) if self.isVertical else 0)
        if (LOBBY_GEOMETRY.startX < self.x() < xMax) and (LOBBY_GEOMETRY.startY < self.y() < yMax):
            new_x = self.x()
            new_y = self.y()

            new_x = (new_x // LOBBY_GEOMETRY.fieldSize * LOBBY_GEOMETRY.fieldSize) + (LOBBY_GEOMETRY.fieldSize // 10)
            new_y = (new_y // LOBBY_GEOMETRY.fieldSize * LOBBY_GEOMETRY.fieldSize) + (LOBBY_GEOMETRY.fieldSize // 10)

            # Проверка, что новые координаты не пересекаются с другими экземплярами MovableLabel
            for label in self.parentWidget().findChildren(MovableShip):
                if label != self and label.geometry().intersects(QRect(new_x, new_y, self.width(), self.height())):
                    return

            # Присвоение списка экземпляров BattleshipButton переменной self.sells
            self.sells = [
                button
                for button in self.parentWidget().findChildren(BattleshipButton)
                if button.geometry().intersects(QRect(new_x, new_y, self.width(), self.height()))
            ]
            self.move(new_x, new_y)
            if self.sells and len(self.sells) == self.shipSize:
                return True

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')
            try:
               self.trySetPos()
            except Exception as e:
                print(e)
