from django.contrib import admin
from django.urls import include, path
from gradykrueger.bot import urls as bot_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tg/", include(bot_urls)),
]
