from django.urls import path
from .views import *

urlpatterns = [
    # path('', index),
    # path('cats/<slug:catid>/', categories),
    path('my-info/', MyInfoView.as_view(), name='myinfo'),
    path('game-state/', GetGameStateView.as_view(), name='get-game-state'),
    path('new-game/', NewGameView.as_view(), name='new-game'),
    path('get-boards/', BoardStateList.as_view(), name='get-boards'),
    path('game-history/', GameHistoryView.as_view(), name='get-game-history'),
    path('send-turn/', SendPlayerTurnView.as_view(), name='send-turn'),
    path('bot-turn/', BotTurnView.as_view(), name='bot-turn'),
    path('my-games/', CheckMyGamesView.as_view(), name='check-my-games'),
    path('try-concede/', PlayerConcede.as_view(), name='try-concede'),
    path('user-info/', UserInfoView.as_view(), name='user-info'),
    path('new-turns/', NewTurnsVies.as_view(), name='new-turns'),
    path('list-my-games/', ListGameStatesView.as_view(), name='list-my-games'),
]
