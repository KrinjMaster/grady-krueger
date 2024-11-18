import time

from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse


class GradyKruegerConfig(AppConfig):
    name = "gradykrueger.bot"
    verbose_name = "Grady Krueger"

    def ready(self):
        global public_url

        from .bot import bot

        if settings.BOT_USE_WEBHOOK:
            print("Bot started in webhook mode")
            # Using webhook
            bot.delete_webhook()
            time.sleep(1)
            # public_url = "https://" + public_url + reverse("gradykrueger_hook")
            # print(public_url)
            # bot.set_webhook(public_url)

        else:
            print("Bot started in polling mode")
            # Using polling
            pass
