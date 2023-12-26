import json

import requests
from http import HTTPStatus
from objects import GlobalObjects
from enum import IntEnum


class CID(IntEnum):
    """Corrupted Ids for tests"""
    nonExistentId = -1
    notMyiD = 73


class User:
    def __init__(self):
        self.myId = 0
        self.myName = ''
        self.shipPositions = []
        self.myBoard = [i for i in range(100)]


class SeaBattleTests:
    def __init__(self):
        self.userOne: User = User()
        self.gObj = GlobalObjects()
        self.cfg = self.gObj.config
        self.getUrl = self.gObj.getApiUrl
        self.session = requests.Session()
        self.gameId = 0
        self.start_tests()

    def login_tests(self):
        url = self.cfg.baseUrl + self.cfg.loginUrl

        def login_test(username, password):
            return requests.post(url, {'username':username, 'password':password})

        assert login_test('qwerty', 'qwert').status_code == HTTPStatus.BAD_REQUEST
        response = login_test('test1', '1234')
        assert response.status_code == HTTPStatus.OK
        assert 'auth_token' in response.json()
        return response.json()['auth_token']

    def init_session(self, token):
        newHeader = {'Authorization': 'Token ' + token}
        self.session.headers.update(newHeader)

    def my_info_tests(self):
        url = self.getUrl('myInfoUrl')
        assert requests.get(url).status_code == HTTPStatus.UNAUTHORIZED
        response = self.session.get(url)
        assert response.status_code == HTTPStatus.OK
        assert 'id' and 'username' in response.json()
        data = response.json()
        self.userOne.myId = data['id']
        self.userOne.myName = data['username']

    def test_concede_url(self, gameId):
        url = self.getUrl('tryConcedeUrl')

        def concede_test(val):
            return self.session.post(url, {'gameId': int(val)}).status_code

        assert requests.post(url).status_code == HTTPStatus.UNAUTHORIZED
        assert concede_test(CID.nonExistentId) == HTTPStatus.NOT_FOUND
        assert concede_test(CID.notMyiD) == HTTPStatus.BAD_REQUEST
        assert concede_test(gameId) == HTTPStatus.OK

    def test_get_active_games(self):
        url = self.getUrl('getActiveGamesUrl')
        assert requests.get(url).status_code == HTTPStatus.UNAUTHORIZED
        response = self.session.get(url)
        assert response.status_code == HTTPStatus.OK
        data = response.json()

        if not data:
            return
        assert 'id' in data
        self.test_concede_url(data['id'])
        assert not self.session.get(url).json()

    def test_new_single_game(self):
        url = self.getUrl('newGameUrl')
        validData = {"1": [[60], [73], [69], [45]], "2": [[63, 64], [33, 34], [87, 88]], "3": [[15, 16, 17], [18, 28, 38]], "4": [[51, 61, 71, 81]]}
        badCount = {"1": [[60], [73], [69], [45], [10]], "2": [[63, 64], [33, 34], [87, 88]], "3": [[15, 16, 17], [18, 28, 38]], "4": [[51, 61, 71, 81]]}
        dupe = {"1": [[60], [73], [69], [45]], "2": [[60, 64], [33, 34], [87, 88]], "3": [[15, 16, 17], [18, 28, 38]], "4": [[51, 61, 71, 81]]}
        badPos = {"1": [[60], [73], [69], [45]], "2": [[60, 74], [33, 34], [87, 88]], "3": [[15, 16, 17], [18, 28, 38]], "4": [[51, 61, 71, 81]]}
        badValue = {"1": [[60], [73], [69], [45]], "2": [[60, 74], [33, 34], [87, 88]], "3": [[15, 16, 170], [18, 28, 38]], "4": [[51, 61, 71, 81]]}
        badValueTwo = {"1": [[-1], [73], [69], [45]], "2": [[60, 74], [33, 34], [87, 88]], "3": [[15, 16, 170], [18, 28, 38]], "4": [[51, 61, 71, 81]]}

        def new_game_test(val, isStatusCode=True):
            val['GameMode'] = 0
            headers = {'Content-Type': 'application/json'}
            data_json = json.dumps(val)
            result = self.session.post(url, data_json, headers=headers)
            return result.status_code if isStatusCode else result

        assert requests.post(url).status_code == HTTPStatus.UNAUTHORIZED
        assert new_game_test(badCount) == HTTPStatus.BAD_REQUEST
        assert new_game_test(dupe) == HTTPStatus.BAD_REQUEST
        assert new_game_test(badPos) == HTTPStatus.BAD_REQUEST
        assert new_game_test(badValue) == HTTPStatus.BAD_REQUEST
        assert new_game_test(badValueTwo) == HTTPStatus.BAD_REQUEST
        response = new_game_test(validData, isStatusCode=False)
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert 'id' in data and data['isSingle'] and not data['winner'] and data['lastTurnNum'] == 0
        self.gameId = data['id']
        assert new_game_test(validData) == HTTPStatus.CONFLICT

    def _boards_and_history(self, url):
        assert requests.get(url).status_code == HTTPStatus.UNAUTHORIZED

        def boards_test(testId, st=True):
            res = self.session.get(url + f'?gameId={int(testId)}')
            return res.status_code if st else res

        assert boards_test(CID.nonExistentId) == HTTPStatus.NOT_FOUND
        assert boards_test(CID.notMyiD) == HTTPStatus.FORBIDDEN
        response = boards_test(self.gameId, False)
        assert response.status_code == HTTPStatus.OK
        return response.json()

    def test_get_boards(self):
        url = self.getUrl('getBoardsUrl')
        data = self._boards_and_history(url)
        assert data['gameId'] == self.gameId and data['ownerId'] == self.userOne.myId and 'shipPositions' in data
        tmpVal = data['shipPositions']
        self.userOne.shipPositions = [value for sublist in tmpVal.values() for inner_list in sublist for value in inner_list]

    def test_get_new_history(self):
        url = self.getUrl('getGameHistoryUrl')
        data = self._boards_and_history(url)
        assert data and data['gameState'] == self.gameId and not data['moveSequence']

    def test_check_game_state(self):
        url = self.getUrl('checkGameUrl')

        def game_state_test(testId, st=True):
            res = self.session.post(url, {'id': int(testId)})
            return res.status_code if st else res

        assert requests.post(url).status_code == HTTPStatus.UNAUTHORIZED
        assert game_state_test(CID.nonExistentId) == HTTPStatus.NOT_FOUND
        assert game_state_test(CID.notMyiD) == HTTPStatus.FORBIDDEN
        response = game_state_test(self.gameId, False)
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data['id'] == self.gameId

    def test_list_my_games(self):
        url = self.getUrl('listMyGamesUrl')

        def my_games_test(index, st=True):
            res = self.session.get(url + f'?index={index}')
            return res.status_code if st else res

        assert my_games_test(-1) == HTTPStatus.BAD_REQUEST
        assert not my_games_test(999, False).json()
        i = 0
        while True:
            data = my_games_test(i, False).json()
            assert data
            if data[-1]['id'] == self.gameId:
                break
            i += 1

    def test_play_single_game(self):
        myLastTurn = -1
        lastTurnNum = 0

        def send_my_turn(testId, action, st=True):
            url = self.getUrl('sendMyTurn')
            res = self.session.post(url, {'gameId': int(testId), 'action': action})
            return res.status_code if st else res

        def get_bot_turn(testId, st=True):
            url = self.getUrl('botTurnUrl')
            res = self.session.post(url, {'gameId': int(testId)})
            return res.status_code if st else res

        def get_valid_turn():
            nonlocal myLastTurn
            myLastTurn += 1
            return myLastTurn

        def get_cur_turn():
            nonlocal lastTurnNum
            lastTurnNum += 1
            return lastTurnNum

        def get_history():
            res = self.session.get(self.getUrl('getGameHistoryUrl') + f'?gameId={self.gameId}')
            assert res.status_code == HTTPStatus.OK
            res = res.json()
            assert res['gameState'] == self.gameId
            return res['moveSequence']

        assert requests.post(self.getUrl('sendMyTurn')).status_code == HTTPStatus.UNAUTHORIZED
        assert requests.post(self.getUrl('botTurnUrl')).status_code == HTTPStatus.UNAUTHORIZED

        assert send_my_turn(CID.nonExistentId, get_valid_turn()) == HTTPStatus.NOT_FOUND
        assert send_my_turn(CID.notMyiD, get_valid_turn()) == HTTPStatus.FORBIDDEN
        assert send_my_turn(self.gameId, -1) == HTTPStatus.BAD_REQUEST
        assert send_my_turn(self.gameId, 100) == HTTPStatus.BAD_REQUEST
        assert get_bot_turn(self.gameId) == HTTPStatus.BAD_REQUEST
        myLastTurn = -1

        def try_player_turn() -> bool:
            hit = True
            while hit:
                responseL = send_my_turn(self.gameId, get_valid_turn(), False)
                assert responseL.status_code == HTTPStatus.OK
                dataL = responseL.json()
                # print(f'player{dataL=}')
                hit = dataL['lastTurn'] // 100
                serverTurn = dataL['lastTurn'] % 100
                history = get_history()
                assert history[-1] == dataL['lastTurn']
                assert dataL['lastTurnNum'] == get_cur_turn() and serverTurn == myLastTurn
                assert dataL['isPlayerOneTurn'] == (True if hit else False)
                if dataL['winner']:
                    return True
                if hit:
                    assert send_my_turn(self.gameId, myLastTurn) == HTTPStatus.BAD_REQUEST
            return False

        def try_bot_turn():
            hit = True
            while hit:
                response = get_bot_turn(self.gameId, False)
                assert response.status_code == HTTPStatus.OK
                dataL = response.json()
                # print(f'bot{dataL=}')
                assert dataL['lastTurnNum'] == get_cur_turn()
                hit = dataL['lastTurn'] // 100
                serverTurn = dataL['lastTurn'] % 100
                if hit:
                    print(f'{self.userOne.shipPositions=}')
                    assert serverTurn in self.userOne.shipPositions
                    self.userOne.shipPositions.remove(serverTurn)

                assert serverTurn in self.userOne.myBoard
                self.userOne.myBoard.remove(serverTurn)
                history = get_history()
                assert history[-1] == dataL['lastTurn']
                if dataL['winner']:
                    return True
                if not hit:
                    assert get_bot_turn(self.gameId) == HTTPStatus.BAD_REQUEST
            return False

        if try_player_turn():
            return

        assert get_bot_turn(CID.nonExistentId) == HTTPStatus.NOT_FOUND
        assert get_bot_turn(CID.notMyiD) == HTTPStatus.FORBIDDEN

        if try_bot_turn():
            return

        while True:
            if try_player_turn() or try_bot_turn():
                response = self.session.post(self.getUrl('checkGameUrl'), {'id':self.gameId})
                assert response.status_code == HTTPStatus.OK
                data = response.json()
                assert data['winner']
                print(f'tests successful. Tested game: {data}')
                break
        pass

    def start_tests(self):
        authToken = self.login_tests()
        self.init_session(authToken)
        self.my_info_tests()
        self.test_get_active_games()
        self.test_new_single_game()
        self.test_get_boards()
        self.test_get_new_history()
        self.test_check_game_state()
        self.test_list_my_games()
        self.test_play_single_game()


if __name__ == '__main__':
    SeaBattleTests()
