from django.contrib import admin
from django.urls import path
from api.views import datos, obtener_datos_clientes


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/datos/', datos),
    path('api/facturas/', obtener_datos_clientes),
]
