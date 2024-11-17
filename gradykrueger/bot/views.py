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
        tbot.process_new_updates([update])

        return HttpResponse("")

    else:
        raise PermissionDenied


@csrf_exempt
def register(request):
    from .bot import bot as tbot

    public_url = getattr(settings, "DOMAIN", "??")
    tbot.delete_webhook()
    time.sleep(1)
    public_url = "https://" + public_url + reverse("??")
    tbot.set_webhook(public_url)
    return HttpResponse(public_url)
