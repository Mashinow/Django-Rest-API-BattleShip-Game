from battleship_button import BattleshipButton
from constants import GAME_RULE, TAB_NAMES, GAME_MODES, TIMER_NAMES
from objects import GlobalObjects
import traceback


class GameManager:
    def __init__(self, obj: GlobalObjects, gameState):
        try:
            print(f'{gameState=}')
            self.gObj = obj
            self.gmCtx = self.gObj.gmCtx
            self.config = self.gObj.config
            self.mySells = {}
            self.enemySells = {}
            self.myShips = {}
            self.gmCtx.turnNum = 0
            self.form = self.gObj.qtObj
            self.gameId = gameState['id']
            self.gameHistory = []
            self.winner = None
            self.isSingle = gameState['isSingle']
            self.myId = self.gmCtx.id
            self.myName = self.gmCtx.name
            self.isPlayerOne = self.myId == gameState['playerOne']
            self.enemyId = gameState['playerTwo'] if self.isPlayerOne else gameState['playerOne']

            self.newGameInit(GAME_MODES.singlePlayer if self.isSingle else GAME_MODES.multiPlayer, self.isPlayerOne)

            self.form.logWindow.move(480, 270)
            self.form.concedeButton.setText('Сдаться')


            myFieldPos = [self.form.myField.x(), self.form.myField.y()]
            enemyFieldPos = [self.form.enemyField.x(), self.form.enemyField.y()]
            self.mySells = self.create_game_sells(*myFieldPos, True)
            self.gObj._waitBotTurn = self.waitBotTurn
            self.enemySells = self.create_game_sells(*enemyFieldPos, False)
            self.get_game_boards()
            self.get_game_history()
            self.setNameLabels()
            self.resetGameHistory(self.gameHistory)
            print(f'{self.gObj.is_your_turn()=}')
            if not self.isSingle:
                self.gObj.createEvent(self.waitMyTurn, 3000, False, TIMER_NAMES.waitMyTurn)

        except Exception as e:
            print(e)
            traceback.print_exc()

    def newGameInit(self, gameMode, isYourTurn):
        ctx = self.gmCtx
        self.gObj.setGameMode(gameMode)
        ctx.enemyName = ''
        self.getEnemyName()
        self.gObj.set_turn(isYourTurn)
        ctx.turnNum = 0

    def waitMyTurn(self):
        if self.winner:
            return
        if not self.gObj.is_your_turn():
            try:
                url = self.gObj.getApiUrl('newTurnsUrl')
                response = self.gObj.reqManager.send_post(url, {'gameId': self.gameId, 'last_turn': self.gmCtx.turnNum}, log=False)
                if response:
                    newTurns = response['turns']
                    self.resetGameHistory(newTurns)

            except Exception as e:
                print(e)
                traceback.print_exc()

        url = self.gObj.getApiUrl('checkGameUrl')
        response = self.gObj.reqManager.send_post(url, {'id': self.gameId})
        if not response:
            raise 'waitMyTurnError'
        self.checkWinner(response)

    def resetGameHistory(self, turns):
        if not turns:
            return
        playerOneBoard, playerTwoBoard = (self.mySells, self.enemySells) if self.isPlayerOne else (self.enemySells, self.mySells)

        ctx = self.gmCtx
        isPlayerOneTurn = (ctx.isYourTurn == self.isPlayerOne)

        print(f'{turns=}')
        for turn in turns:
            isHasShip = bool(turn // 100)
            cellPos = turn % 100
            if isPlayerOneTurn:
                curCell = playerTwoBoard[cellPos]
            else:
                curCell = playerOneBoard[cellPos]
            curCell.set_has_ship(isHasShip)
            curCell.attack_process()
            if not isHasShip:
                isPlayerOneTurn = not isPlayerOneTurn
        self.gObj.set_turn(isPlayerOneTurn == self.isPlayerOne)

    def tryConcede(self):
        if self.winner:
            self.form.logWindow.move(990, 30)
            self.gObj.set_active_tab(TAB_NAMES.main)
        else:
            url = self.gObj.getApiUrl('tryConcedeUrl')
            response = self.gObj.reqManager.send_post(url, {'gameId': self.gameId})
            if response:
                self.checkWinner(response)

    def checkWinner(self, gameState):
        if gameState['winner'] is not None:
            ctx = self.gmCtx
            wnr = gameState['winner']
            winner = ctx.name if ((wnr == 1 and self.isPlayerOne) or (wnr == 2 and not self.isPlayerOne)) else ctx.enemyName
            self.gObj.send_log_msg(f'Ход {ctx.turnNum}: Победил {winner}\nКонец Игры')
            self.winner = winner
            form = self.gObj.qtObj
            form.concedeButton.setText('Меню')

    def waitBotTurn(self):
        print('start Bot turn')
        url = self.gObj.getApiUrl('botTurnUrl')
        response = self.gObj.reqManager.send_post(url, {'gameId': self.gameId}, log=False)
        if not response:
            return
        enemyTurn = response['lastTurn']

        self.mySells[enemyTurn % 100].attack_process()
        self.checkWinner(response)
        self.gObj.set_turn((self.isPlayerOne == response['isPlayerOneTurn']))
        print(f'end bot turn {response}')

    def getEnemyName(self):
        ctx = self.gObj.gmCtx
        if ctx.enemyName:
            return ctx.enemyName

        if self.isSingle:
            ctx.enemyName = 'Bot'
        else:
            url = self.gObj.getApiUrl('userInfoUrl')
            response = self.gObj.reqManager.send_get(url, {'id': self.enemyId})
            if response:
                ctx.enemyName = response['username']
        return ctx.enemyName

    def setNameLabels(self):
        form = self.gObj.qtObj
        form.player1Name.setText(f'Player: {self.gObj.gmCtx.name}')
        form.player2Name.setText(f'Player: {self.getEnemyName()}')

    def buttonAttackProcess(self, buttonNum):
        print('start Player Turn')
        try:
            url = self.gObj.getApiUrl('sendMyTurn')
            response = self.gObj.reqManager.send_post(url, {'gameId': self.gameId, 'action': buttonNum})
            if not response:
                return
            myTurn = response['lastTurn']
            if myTurn//100 == 1:
                self.enemySells[myTurn % 100].set_has_ship(True)
            self.enemySells[myTurn % 100].attack_process()
            self.checkWinner(response)
            self.gObj.set_turn(self.isPlayerOne == response['isPlayerOneTurn'])
            print(f'end Player Turn {response}')
        except Exception as e:
            print('abc')
            print(e)
            traceback.print_exc()

    def get_game_history(self):
        url = self.gObj.getApiUrl('getGameHistoryUrl') + f'?gameId={self.gameId}'
        response = self.gObj.reqManager.send_get(url)
        if not response:
            raise 'game history not found'
        self.gameHistory = response['moveSequence']

    def get_game_boards(self):
        url = self.gObj.getApiUrl('getBoardsUrl') + f'?gameId={self.gameId}'
        response = self.gObj.reqManager.send_get(url)
        if not response:
            raise 'game boards not found'
        self.myShips = response
        myShips = [value for sublist in self.myShips['shipPositions'].values() for inner_list in sublist for value in inner_list]
        for ship in myShips:
            self.mySells[ship].set_has_ship(True)

    def create_game_sells(self, startX, startY, isMyField):
        startX += 5; startY += 5
        elemSize = [30, 30]
        offs = 5
        cellsDict = {}
        for i in range(GAME_RULE.fieldCountX):
            for j in range(GAME_RULE.fieldCountY):
                new_button = BattleshipButton(i, j, self.form.tabGame, self.gObj, isMyField)
                posX = startX + ((elemSize[0] + offs) * i)
                posY = startY + ((elemSize[1] + offs) * j)
                new_button.setGeometry(posX, posY, *elemSize)
                new_button.show()
                cellsDict[i + j*10] = new_button
        return cellsDict
