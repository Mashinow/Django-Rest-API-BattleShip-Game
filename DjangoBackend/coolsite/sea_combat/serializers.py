from rest_framework import serializers
from .models import GameState, BoardState, GameMoveHistory


class GameStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameState
        fields = ['id', 'isSingle', 'playerOne', 'playerTwo', 'isPlayerOneTurn', 'winner', 'lastTurn', 'lastTurnNum']


class BoardStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardState
        fields = ['gameId', 'ownerId', 'shipPositions']


class GameHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GameMoveHistory
        fields = ['gameState', 'moveSequence']
