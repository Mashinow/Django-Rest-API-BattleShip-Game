from PyQt5.QtCore import QTimer
from constants import GAME_MODES, TIMER_NAMES


class GlobalObjects:
    def __init__(self):
        from config import LocalConfig
        from request_manager import RequestManager
        from game_context import GameContext
        self.config = LocalConfig()
        self.reqManager = RequestManager(self)
        self.qtObj = None
        self.window = None
        self._logWindow = None
        self.gmCtx = GameContext()
        self.gameManager = None
        self.historyManager = None
        self._waitBotTurn = None

    def init_qt_obj(self, form):
        self.qtObj = form
        self._logWindow = form.logWindow

    def send_log_msg(self, msg):
        self._logWindow.appendPlainText(str(msg))

    def is_your_turn(self) -> bool:
        return self.gmCtx.isYourTurn

    def set_turn(self, isYourTurn: bool):
        ctx = self.gmCtx
        ctx.isYourTurn = isYourTurn
        self.qtObj.curTurn.setText(f'Сейчас ходит: {ctx.name if isYourTurn else ctx.enemyName}')
        if self.getGameMode() == GAME_MODES.singlePlayer and not isYourTurn:
            self.createEvent(self._waitBotTurn, 3000, True, TIMER_NAMES.botTurn)

    def getGameMode(self):
        return self.gmCtx.gameMode

    def createEvent(self, targetFunc, timeout, isSingle, timerName):
        qWidget = self.window
        timer = QTimer(qWidget)
        timer.timeout.connect(targetFunc)
        timer.setSingleShot(isSingle)
        timer.start(timeout)
        setattr(qWidget, timerName, timer)

    def removeEvent(self, timerName):
        qWidget = self.window
        if hasattr(qWidget, timerName):
            timer = getattr(qWidget, timerName)
            timer.stop()
            timer.deleteLater()
            delattr(qWidget, timerName)

    def setGameMode(self, newMode):
        self.gmCtx.gameMode = newMode

    def set_active_tab(self, newNum: int):
        for i in range(0, self.qtObj.tabWidget.count()):
            if i == newNum:
                continue
            self.qtObj.tabWidget.setTabEnabled(i, False)
        self.qtObj.tabWidget.setTabEnabled(newNum, True)
        self.qtObj.tabWidget.setCurrentIndex(newNum)

    def get_active_tab(self):
        return self.qtObj.tabWidget.currentIndex()

    def getApiUrl(self, name):
        return self.config.baseUrl + self.config.apiUrl + getattr(self.config, name)
