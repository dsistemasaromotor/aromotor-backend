from django.contrib import admin
from django.urls import path
from api.views import datos


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/datos/', datos),
]
