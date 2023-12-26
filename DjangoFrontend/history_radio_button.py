from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QRadioButton
from objects import GlobalObjects


class HistoryRadioButton(QRadioButton):
    def __init__(self, text, number, obj: GlobalObjects, parent=None):
        super().__init__(text, parent)
        self.gObj = obj
        self.number = number
        self.clicked.connect(self.handle_click)

        font = QFont()
        font.setPointSize(11)
        self.setFont(font)

    def handle_click(self):
        self.gObj.historyManager.show_history(self.number)
