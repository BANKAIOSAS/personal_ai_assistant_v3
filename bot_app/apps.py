import os
from django.apps import AppConfig


class BotAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_app'

    def ready(self):
        if os.environ.get('RUN_MAIN'):
            from .tg_bot import run_bot_in_thread
            run_bot_in_thread()

