import json
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import GameState, BoardState, GameMoveHistory
from .serializers import GameStateSerializer, BoardStateSerializer, GameHistorySerializer
import game_manager as gm


def check_winners(gameState):
    if gameState.winner:
        if gameState.id not in gm.ActiveGames:
            return
        gameManager = gm.ActiveGames.pop(gameState.id)
        if gameManager:
            del gameManager


def check_participation(request, game_state):
    if request.user != game_state.playerOne and request.user != game_state.playerTwo:
        return Response({"error": "You are not a participant of this game."}, status=status.HTTP_403_FORBIDDEN)
    else:
        return None


class MyInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'username': user.username,
        }
        return Response(data)


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pk = request.query_params.get('id', None)
            user = User.objects.get(pk=pk)
            data = {
                'id': user.id,
                'username': user.username,
            }
            return Response(data)
        except Exception as e:
            print(e)
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class GetGameStateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        game_id = request.data.get('id')
        game_state = get_object_or_404(GameState, id=game_id)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        serializer = GameStateSerializer(game_state)
        return Response(serializer.data)


class NewGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        existing_game_as_player_one = GameState.objects.filter(playerOne=request.user, winner__isnull=True).first()
        existing_game_as_player_two = GameState.objects.filter(playerTwo=request.user, winner__isnull=True).first()
        existing_game = existing_game_as_player_one if existing_game_as_player_one else existing_game_as_player_two
        if existing_game:
            if existing_game.id not in gm.PlayersQueue:
                gm.PlayersQueue[existing_game.id] = existing_game
            return Response('Your game already exists', 409)
            # serializer = GameStateSerializer(existing_game)
            # return Response(serializer.data)

        data = json.loads(request.body)

        ship_data = {}
        for key, value in data.items():
            if key != "GameMode":
                ship_data[key] = value

        if not (gm.ships_validate(ship_data)):
            return Response({"error": "Invalid ships data"}, status=400)

        game_mode = data['GameMode']

        is_single = (game_mode == 0)
        isTwoPlayer = False
        if not is_single and len(gm.PlayersQueue) > 0:
            key, new_game = gm.PlayersQueue.popitem()
            if new_game.playerTwo is None:
                new_game.playerTwo = request.user
                new_game.save()
                isTwoPlayer = True
            else:
                return Response({"error": "Invalid game data"}, status=400)
        else:
            new_game = GameState.objects.create(
                playerOne=request.user,
                isSingle=is_single,
            )

        BoardState.objects.create(
            gameId=new_game,
            ownerId=request.user,
            shipPositions=ship_data
        )

        if is_single or isTwoPlayer:
            gm.ActiveGames[new_game.id] = gm.GameManager(new_game)
        else:
            gm.PlayersQueue[new_game.id] = new_game

        serializer = GameStateSerializer(new_game)
        return Response(serializer.data)


class BoardStateList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        gameId = request.query_params.get('gameId', None)
        if gameId is None:
            return Response({"error": "Game ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        game_state = get_object_or_404(GameState, id=gameId)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        board_state = BoardState.objects.filter(gameId=gameId, ownerId=request.user).first()
        serializer = BoardStateSerializer(board_state)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        gameId = request.query_params.get('gameId', None)
        if gameId is None:
            return Response({"error": "Game ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        game_state = get_object_or_404(GameState, id=gameId)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        gameHistory = GameMoveHistory.objects.filter(gameState=game_state).first()
        serializer = GameHistorySerializer(gameHistory)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SendPlayerTurnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Retrieve the game ID and action from the request
        game_id = request.data.get('gameId')
        action = request.data.get('action')

        if game_id is None or action is None:
            return Response({"error": "Game ID or action are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the game state object
        game_state = get_object_or_404(GameState, id=game_id)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        # Retrieve the game manager for the current game
        game_manager = gm.get_game_manager(game_state)
        if not game_manager:
            return Response({"error": "Game manager not found for this game."}, status=status.HTTP_404_NOT_FOUND)

        # Call the try_turn function
        result = game_manager.try_turn(request.user, int(action))
        if not result:
            return Response({"error": "Invalid turn data"}, status=400)

        serializer = GameStateSerializer(result)
        return Response(serializer.data)


class PlayerConcede(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        game_id = request.data.get('gameId')

        if game_id is None:
            return Response({"error": "Game ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the game state object
        game_state = get_object_or_404(GameState, id=game_id)
        if game_state.winner:
            return Response({"error": "This game is already over."}, status=status.HTTP_400_BAD_REQUEST)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        game_state.winner = 2 if game_state.playerOne == request.user else 1
        game_state.save()
        GameStateSerializer(game_state)
        check_winners(game_state)
        serializer = GameStateSerializer(game_state)
        return Response(serializer.data)


class BotTurnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        game_id = request.data.get('gameId')

        if game_id is None:
            return Response({"error": "Game ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the game state object
        game_state = get_object_or_404(GameState, id=game_id)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        # Retrieve the game manager for the current game
        game_manager = gm.get_game_manager(game_state)
        if not game_manager:
            return Response({"error": "Game manager not found for this game."}, status=status.HTTP_404_NOT_FOUND)

        result = game_manager.get_enemy_turn()

        if not result:
            return Response({"error": "Invalid turn data"}, status=400)

        serializer = GameStateSerializer(result)
        return Response(serializer.data)


class CheckMyGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Извлекаем игры, где пользователь является одним из игроков и игра активна (нет победителя)
        games = GameState.objects.filter(
            (Q(playerOne=request.user) | Q(playerTwo=request.user)),
            winner__isnull=True
        ).order_by('-id')  # Сортировка по убыванию ID, чтобы получить последнюю игру

        # Если есть активные игры
        if games.exists():
            # Если найдено больше одной активной игры
            if games.count() > 1:
                # Устанавливаем пользователя как проигравшего во всех играх, кроме последней
                for game in games[1:]:
                    game.winner = 2 if game.playerOne == request.user else 1
                    game.save()

            # Возвращаем последнюю игру
            serializer = GameStateSerializer(games.first())
            return Response(serializer.data)
        else:
            return Response({})


class NewTurnsVies(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Retrieve the game ID and action from the request
        game_id = request.data.get('gameId')
        last_turn = request.data.get('last_turn')
        if game_id is None or last_turn is None:
            return Response({"error": "Game ID are required."}, status=status.HTTP_400_BAD_REQUEST)
        game_state = get_object_or_404(GameState, id=game_id)

        res = check_participation(request, game_state)
        if res is not None:
            return res

        game_manager = gm.get_game_manager(game_state)
        if not game_manager:
            return Response({"error": "Game manager not found for this game."}, status=status.HTTP_404_NOT_FOUND)

        return Response({'turns': game_manager.get_new_turns(int(last_turn))})


class ListGameStatesView(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Get the index from the request, defaulting to 0 if not provided
        index = int(request.query_params.get('index', 0))

        if index < 0:
            return Response('index must be >= 0', 400)

        # Calculate the offset based on the index
        offset = index * 15

        # Fetch up to 15 GameState instances where the user is playerOne or playerTwo
        game_states = GameState.objects.filter(
            Q(playerOne=request.user) | Q(playerTwo=request.user)
        ).order_by('id')[offset:offset + 15]

        # Serialize the game states
        serializer = GameStateSerializer(game_states, many=True)

        # Return the serialized data
        return Response(serializer.data)