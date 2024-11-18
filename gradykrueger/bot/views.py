import time

import telebot
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def handler(request):
    from .bot import bot as tbot

    if request.META["CONTENT_TYPE"] == "application/json":

        json_data = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_data)

        if update is not None:
            tbot.process_new_updates([update])

            return HttpResponse(content=b"")
    else:
        raise PermissionDenied


@csrf_exempt
def register(request):
    from .bot import bot as tbot

    CERTIFICATE = join(settings.BASE_DIR, "PUBLIC.pem")

    public_url = settings.DEV_DOMAIN
    tbot.delete_webhook()
    time.sleep(1)
    public_url = "http://" + public_url + reverse("gradykrueger_hook")
    tbot.set_webhook(public_url, certificate=CERTIFICATE)
    return HttpResponse(public_url)
