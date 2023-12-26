import random

from sea_combat.models import BoardState, GameMoveHistory


class GameManager:
    def __init__(self, gameState):
        self.gameState = gameState
        self.isSingle = gameState.isSingle
        self.isPlayerOneTurn = True
        boardData = BoardState.objects.filter(gameId=gameState.id, ownerId=gameState.playerOne).first()
        self.shipsOne = boardData.shipPositions
        self.boardOne = [i for i in range(100)]
        self.boardTwo = [i for i in range(100)]
        self.curTurn = 0

        if self.isSingle:
            self.shipsTwo = self.create_bot_board()
        else:
            boardData = BoardState.objects.filter(gameId=gameState.id, ownerId=gameState.playerTwo).first()
            self.shipsTwo = boardData.shipPositions

        self.gameHistory = GameMoveHistory.objects.filter(gameState=self.gameState).first()
        if not self.gameHistory:
            self.gameHistory = GameMoveHistory.objects.create(
                gameState=self.gameState,
                moveSequence=[]
            )

        self.shipsOne = [value for sublist in self.shipsOne.values() for inner_list in sublist for value in inner_list]
        self.shipsTwo = [value for sublist in self.shipsTwo.values() for inner_list in sublist for value in inner_list]
        self.reset_game_history()

    def get_new_turns(self, lastTurn) -> list:
        if (self.curTurn - lastTurn) <= 0:
            return []
        new_turns_count = self.curTurn - lastTurn
        return self.gameHistory.moveSequence[-new_turns_count:]

    def reset_game_history(self):
        for turn in self.gameHistory.moveSequence:
            player = self.gameState.playerOne if self.isPlayerOneTurn else self.gameState.playerTwo
            self.update_game_state(player, turn % 100)

    def get_enemy_turn(self):
        if not self.isSingle or self.isPlayerOneTurn:
            return False
        return self.try_turn(None, random.choice(self.boardOne))

    def update_game_state(self, player, action: int):
        isPlayerOne = player == self.gameState.playerOne
        if isPlayerOne != self.isPlayerOneTurn:
            print('isPlayerOne != self.isPlayerOneTurn')
            return False

        targetBoard = self.boardTwo if isPlayerOne else self.boardOne
        targetShips = self.shipsTwo if isPlayerOne else self.shipsOne

        if action not in targetBoard:
            print('action not in targetBoard')
            return False

        resultTurn = action
        if action not in targetShips:
            self.isPlayerOneTurn = not self.isPlayerOneTurn
        else:
            resultTurn += 100
            targetShips.remove(action)

        targetBoard.remove(action)
        self.curTurn += 1
        return [resultTurn, targetShips, isPlayerOne]

    def try_turn(self, player, action: int):
        result = self.update_game_state(player, action)
        if result:
            resultTurn = result[0]
            targetShips = result[1]
            isPlayerOne = result[2]
            self.gameState.isPlayerOneTurn = self.isPlayerOneTurn
            self.gameState.lastTurn = resultTurn
            self.gameState.lastTurnNum = self.curTurn
            if len(targetShips) == 0:
                self.gameState.winner = 1 if isPlayerOne else 2
            self.gameHistory.moveSequence.append(resultTurn)
            self.gameHistory.save()
            self.gameState.save()
            return self.gameState
        return False

    def create_bot_board(self):
        ships_dict = self._generate_ships()
        boardData = BoardState.objects.filter(gameId=self.gameState.id, ownerId=self.gameState.playerTwo).first()
        if boardData:
            return boardData.shipPositions
        else:
            BoardState.objects.create(
                gameId=self.gameState,
                shipPositions=ships_dict
            )
            return ships_dict

    def _generate_ships(self):
        """
        Generates a dictionary of ships according to the specified rules:
        - Range of coordinates: 0-99
        - 4 ships of length 1, 3 ships of length 2, 2 ships of length 3, 1 ship of length 4
        - Ships are either horizontal or vertical, not diagonal or disjointed
        - Occupied cells must not overlap
        """

        def is_valid_position(ship, occupied_cells):
            """
            Checks if a ship's position is valid (not overlapping and within the board).
            """
            for coord in ship:
                if coord in occupied_cells or not (0 <= coord // 10 < 10 and 0 <= coord % 10 < 10):
                    return False
            return True

        def place_ship(length, occupied_cells):
            """
            Places a ship of a given length on the board.
            """
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    x = random.randint(0, 9 - length)
                    y = random.randint(0, 9)
                    ship = [x + i + 10 * y for i in range(length)]
                else:
                    x = random.randint(0, 9)
                    y = random.randint(0, 9 - length)
                    ship = [x + 10 * (y + i) for i in range(length)]

                if is_valid_position(ship, occupied_cells):
                    occupied_cells.update(ship)
                    return ship

        occupied_cells = set()
        ships = {"1": [], "2": [], "3": [], "4": []}

        # Placing ships according to the rules
        for i in range(4):
            ships["1"].append(place_ship(1, occupied_cells))
        for i in range(3):
            ships["2"].append(place_ship(2, occupied_cells))
        for i in range(2):
            ships["3"].append(place_ship(3, occupied_cells))
        ships["4"].append(place_ship(4, occupied_cells))

        return ships


ActiveGames = {}
PlayersQueue = {}


def _is_valid_ship(ship):
    """
    Validate if a ship is placed correctly (either horizontal or vertical and continuous).
    """
    if len(ship) == 1:
        return True  # Single cell ship is always valid

    ship = sorted(ship)
    is_horizontal = all(x // 10 == ship[0] // 10 for x in ship)
    is_vertical = all(x % 10 == ship[0] % 10 for x in ship)

    if not (is_horizontal or is_vertical):
        return False  # Ship is neither horizontal nor vertical

    # Check if the ship cells are continuous
    return all(ship[i] + 1 == ship[i + 1] for i in range(len(ship) - 1)) if is_horizontal else \
           all(ship[i] + 10 == ship[i + 1] for i in range(len(ship) - 1))


def ships_validate(board: dict):
    """
    Validate the battleship board.
    Ensures that all coordinates are within 0-99, the number and lengths of ships are correct,
    ships are either horizontal or vertical, and no two ships occupy the same space.
    """
    required_ships = {1: 4, 2: 3, 3: 2, 4: 1}  # Required ships of each length
    occupied_cells = set()

    for ship_length, ships in board.items():
        ship_length = int(ship_length)

        # Check if the number of ships of this length is correct
        if len(ships) != required_ships[ship_length]:
            return False

        for ship in ships:
            # Check if the ship's length is correct
            if len(ship) != ship_length:
                return False

            # Check if the ship's coordinates are within the range and the ship is placed correctly
            if not all(0 <= coord < 100 for coord in ship) or not _is_valid_ship(ship):
                return False

            # Check for overlapping ships
            ship_set = set(ship)
            if ship_set & occupied_cells:
                return False
            occupied_cells.update(ship_set)
    return True


def get_game_manager(gameState):
    if gameState.winner:
        return None
    if gameState.id not in ActiveGames:
        ActiveGames[gameState.id] = GameManager(gameState)
    return ActiveGames[gameState.id]
