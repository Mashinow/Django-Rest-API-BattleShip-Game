from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class GameState(models.Model):
    isSingle = models.BooleanField(default=True)
    playerOne = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='game_states_as_player_one')
    playerTwo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='game_states_as_player_two')
    isPlayerOneTurn = models.BooleanField(default=True)
    winner = models.IntegerField(null=True, blank=True)
    lastTurn = models.IntegerField(default=0)
    lastTurnNum = models.IntegerField(default=0)

    def __str__(self):
        return f"Game {self.id}"


class BoardState(models.Model):
    gameId = models.ForeignKey(GameState, on_delete=models.CASCADE)
    ownerId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    shipPositions = models.JSONField()

    def __str__(self):
        return f"BoardState for Game {self.gameId.id}"


class GameMoveHistory(models.Model):
    gameState = models.OneToOneField(GameState, on_delete=models.CASCADE, primary_key=True)
    moveSequence = models.JSONField()

    def __str__(self):
        return f"Move History for Game {self.gameState.id}"
