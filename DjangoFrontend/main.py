import json
import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic

from game_manager import GameManager
from history_manager import HistoryManager
from lobby_manager import LobbyManager
from objects import GlobalObjects
from constants import TAB_NAMES, GAME_MODES, TIMER_NAMES

import traceback

class MainInterface:
    def __init__(self):

        # attrs--------------
        self.form = None
        self.gObj = GlobalObjects()
        self.lobbyMngr = None
        self.gameMngr = None
        self.historyMngr = None
        self.window = None
        self.set_active_tab = self.gObj.set_active_tab
        # -------------------

        self.init_qt_screen()

    # utils functions -------------
    def get_login_pwd(self):
        return [self.form.loginText.text(), self.form.passText.text()]

    def set_login_pwd(self):
        config = self.gObj.config
        if config.login and config.password:
            self.form.loginText.setText(config.login)
            self.form.passText.setText(config.password)
        self.form.saveLogPass.setChecked(config.isLoginSave)

    def update_iface_from_config(self):
        self.set_login_pwd()

    def start_game(self, gameState):
        self.set_active_tab(TAB_NAMES.game)
        self.gameMngr = GameManager(self.gObj, gameState)
        self.gObj.gameManager = self.gameMngr

    def try_start_game(self, shipsDict):
        self.gObj.send_log_msg('Корабли установлены, игра скоро начнется')
        url = self.gObj.getApiUrl('newGameUrl')
        response = self.gObj.reqManager.send_json_post(url, shipsDict, False)
        if not response:
            self.get_active_game()
        else:
            self.game_preparation(response)

    def waiting_two_player(self, gameId):
        try:
            url = self.gObj.getApiUrl('checkGameUrl')
            response = self.gObj.reqManager.send_post(url, {'id': gameId})
            if response:
                if response['playerTwo']:
                    self.gObj.removeEvent(TIMER_NAMES.waitPlayer)
                    self.start_game(response)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def game_preparation(self, response):
        if response:
            # print(response)
            # self.gObj.gmCtx.gameMode = response['isSingle']
            if not response['isSingle'] and not response['playerTwo']:
                self.gObj.set_active_tab(TAB_NAMES.lobby)
                self.form.waitingWindow.setVisible(True)
                self.form.waitingWindow.raise_()
                self.gObj.createEvent(lambda: self.waiting_two_player(response['id']), 5000, False, TIMER_NAMES.waitPlayer)
            elif response['isSingle'] or response['playerTwo']:
                self.start_game(response)

    def get_my_info(self):
        src = self.gObj.getApiUrl('myInfoUrl')
        response = self.gObj.reqManager.send_get(src)
        if not response:
            raise 'error get my info'
        self.gObj.gmCtx.name = response['username']
        self.gObj.gmCtx.id = response['id']

    def get_active_game(self):
        url = self.gObj.getApiUrl('getActiveGamesUrl')
        response = self.gObj.reqManager.send_get(url)
        if response:
            self.game_preparation(response)
    # -----------------------------

    # button functions -------------
    def login_func(self):
        try:
            login, password = self.get_login_pwd()
            if self.gObj.reqManager.login_process(login, password):
                self.gObj.send_log_msg('login success')

                isSave: bool = self.form.saveLogPass.isChecked()
                if not isSave:
                    login = ''
                    password = ''
                self.gObj.config.update_json_file({"login": login, "password": password, "isLoginSave": isSave})
                self.set_active_tab(TAB_NAMES.main)
                self.get_my_info()
                self.get_active_game()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def goto_lobby(self, gameMode):
        self.form.waitingWindow.setVisible(False)
        self.lobbyMngr = LobbyManager(self.gObj)
        self.set_active_tab(TAB_NAMES.lobby)
        self.gObj.setGameMode(gameMode)

    def single_func(self):
        self.goto_lobby(GAME_MODES.singlePlayer)

    def multi_func(self):
        self.goto_lobby(GAME_MODES.multiPlayer)

    def menu2_func(self):
        self.set_active_tab(TAB_NAMES.main)

    def menu_func(self):
        del self.lobbyMngr
        self.set_active_tab(TAB_NAMES.main)

    def lRandom_func(self):
        self.lobbyMngr.randomize_labels()

    def lReset_func(self):
        self.menu_func()
        self.single_func()

    def lConfirm_func(self):
        shipsDict = self.lobbyMngr.try_confirm_ships()
        if not shipsDict:
            return
        try:
            self.try_start_game(shipsDict)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def concede_func(self):
        self.gameMngr.tryConcede()

    def toLogin_func(self):
        self.gObj.set_active_tab(TAB_NAMES.login)

    def history_func(self):
        if not self.historyMngr:
            self.historyMngr = HistoryManager(self.gObj)
            self.gObj.historyManager = self.historyMngr
        else:
            self.historyMngr._set_history_page(0)
            self.form.historyLog.setPlainText('Здесь выводится история игр.\nВыберите игру ->')
            self.historyMngr.disable_radio_button()
        self.gObj.set_active_tab(TAB_NAMES.history)

    def historyL_func(self):
        self.historyMngr.set_history_page(-1)

    def historyR_func(self):
        self.historyMngr.set_history_page(1)

    def test_func(self):
        try:
            self.goto_lobby(GAME_MODES.singlePlayer)
            # url = self.gObj.getApiUrl('listMyGamesUrl')
            # print(self.gObj.reqManager.send_get(url, {'index': 2}))
        except Exception as e:
            print(e)
            traceback.print_exc()
    #  ----------------------------

    def init_buttons(self):
        rawButtons = dir(self)
        tmpList = [string for string in rawButtons if string.endswith("_func")]
        funcNames = [string[:-5] for string in tmpList]
        for funcName in funcNames:
            getattr(self.form, f'{funcName}Button').clicked.connect(getattr(self, f'{funcName}_func'))

    def init_qt_screen(self):
        app = QApplication(sys.argv)
        Form, Window = uic.loadUiType(os.getcwd() + '\\interface\\untitled.ui')

        class MyWindow(Window):
            def __init__(self):
                super(MyWindow, self).__init__()

            def closeEvent(self, event):
                # todo add logout
                sys.exit()

        window = MyWindow()
        self.window = window
        self.gObj.window = window
        window.show()
        self.form = Form()
        self.form.setupUi(window)
        self.init_buttons()
        self.gObj.init_qt_obj(self.form)
        self.set_active_tab(TAB_NAMES.login)
        self.update_iface_from_config()
        # Create a movable QLabel
        # movable_label = MovableLabel('', self.form.tabLobby, QSize(100, 30))
        if not self.gObj.config.debug:
            self.form.testButton.hide()
        sys.exit(app.exec_())


if __name__ == '__main__':
    MainInterface()
