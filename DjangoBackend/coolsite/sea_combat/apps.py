from django.apps import AppConfig
import warnings


class SeaCombatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sea_combat'

    def ready(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            isMakeMigration = False
            from .models import GameState
            from game_manager import PlayersQueue

            if not isMakeMigration:
                games = GameState.objects.filter(isSingle=False, playerTwo__isnull=True)
                for game in games:
                    PlayersQueue[game.id] = game