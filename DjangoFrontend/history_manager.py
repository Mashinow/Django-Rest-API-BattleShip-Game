import traceback
from typing import List, Dict
from PyQt5.QtWidgets import QVBoxLayout

from history_radio_button import HistoryRadioButton
from objects import GlobalObjects


class HistoryManager:
    def __init__(self, obj: GlobalObjects):
        self.gObj = obj
        self.buttons = {}
        self.add_radio_buttons()
        self.userNames = {None: 'bot'}
        self.lastRequest: List[Dict[str, any]] = []
        try:
            self._set_history_page(0)
        except Exception as e:
            print(e)
            traceback.print_exc()
        pass

    def show_history(self, num):
        try:
            if not self.lastRequest or len(self.lastRequest) < num:
                return
            gameData = self.lastRequest[num]
            gameId = gameData['id']
            url = self.gObj.getApiUrl('getGameHistoryUrl')
            response = self.gObj.reqManager.send_get(url, {'gameId': gameId})
            if not response:
                raise 'show history error'
            resStr = self.create_history_list(gameData, response['moveSequence'])
            self.gObj.qtObj.historyLog.setPlainText(resStr)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def create_history_list(self, gameData, gameHistory):
        curDict = 'ABCDEFGHIJ'
        players = []
        ids = [gameData['playerOne'], gameData['playerTwo']]
        for userId in ids:
            players.append(self.userNames[userId] if userId in self.userNames else self.get_name_from_id(userId))
        curTurnOwn = 0
        curTurnNum = 0
        winner = gameData['winner']
        winner = players[winner-1]
        resList = []
        for turn in gameHistory:
            curTurnNum += 1
            curPlayer = players[curTurnOwn]
            isHit = bool(turn // 100)
            attackRes = 'попал' if isHit else 'мимо'
            target = f'{turn % 100:02}'[::-1]
            target = curDict[int(target[0])] + target[1]
            resList.append(f'Ход {curTurnNum}: {curPlayer} атаковал {target} результат {attackRes}')
            if not isHit:
                curTurnOwn = curTurnOwn ^ 1
        resList.append(f'Ход {curTurnNum}: Победил {winner}')
        resList.append(f'Конец Игры')
        resStr = '\n'.join(resList)
        return resStr

    def get_name_from_id(self, userId):
        url = self.gObj.getApiUrl('userInfoUrl')
        response = self.gObj.reqManager.send_get(url, {'id': userId})
        if response:
            name = response['username']
            self.userNames[userId] = name
            return name

    def convert_game_state(self, data):
        ctx = self.gObj.gmCtx
        players = []
        ids = [data['playerOne'], data['playerTwo']]
        for userId in ids:
            players.append(self.userNames[userId] if userId in self.userNames else self.get_name_from_id(userId))

        myIndex = ids.index(ctx.id)
        winner = data['winner']
        winner = players[winner-1]
        gameId = data['id']
        resStr = f'Игра №{gameId}: {players.pop(myIndex)} vs {players[0]}. Победа: {winner}'
        return resStr

    def set_history_page(self, offset):
        try:
            pageLabel = self.gObj.qtObj.historyPage
            curPage = int(pageLabel.text())
            newPage = curPage + offset - 1
            if newPage < 0:
                return
            if self._set_history_page(newPage):
                pageLabel.setText(f'{newPage+1}')
                self.disable_radio_button()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def disable_radio_button(self):
        self.buttons[15].setChecked(True)

    def _set_history_page(self, page):
        try:
            url = self.gObj.getApiUrl('listMyGamesUrl')
            response = self.gObj.reqManager.send_get(url, {'index': page})
            if response:
                self.lastRequest = response
                for index, history in enumerate(response):
                    resStr = self.convert_game_state(history)
                    self.buttons[index].setText(resStr)
                for i in range(index + 1, 15):
                    self.buttons[i].setText('')
                return True
            else:
                return False

        except Exception as e:
            print(e)
            traceback.print_exc()

    def add_radio_buttons(self):
        form = self.gObj.qtObj

        layout = QVBoxLayout(form.widgetHistory)

        for i in range(16):
            # Создаем радиокнопку
            radio_button = HistoryRadioButton('', i, self.gObj, form.widgetHistory)
            self.buttons[i] = radio_button
            # Добавляем радиокнопку в layout
            layout.addWidget(radio_button)

            # Устанавливаем размер радиокнопки в процентах от размера widgetHistory
            radio_button_width = int(form.widgetHistory.width() * 0.8)
            radio_button_height = int(form.widgetHistory.height() / 15)
            radio_button.resize(radio_button_width, radio_button_height)
        self.buttons[15].hide()
        form.widgetHistory.setLayout(layout)
