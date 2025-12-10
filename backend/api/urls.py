from django.urls import path
from .views import obtener_cxc_aromotor
from api import views as api_views
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [
    path('obtener-cxc/', obtener_cxc_aromotor),
    path("user/token/", api_views.MyTokenObtainPairView.as_view()),
    path("user/token/refresh/", TokenRefreshView.as_view()),
    path("users/", api_views.UsersList.as_view(), name="Listado de usuarios"),
    path("user/registro/", api_views.RegistroUsuarioView.as_view(), name="Crear nuevo usuario"),

    path('crear-usuario/', views.CrearUsuarioSinPasswordView.as_view(), name='crear_usuario_sin_password'),
     path('users/<int:id>/', views.EditarUsuarioView.as_view(), name='editar_usuario'),
     path('perfiles/', views.ListarPerfilesView.as_view(), name='listar_perfiles'), 
    path('set-password/', views.SetPasswordView.as_view(), name='set_password'),
    path('generar-enlace-reset/', views.GenerarEnlaceResetView.as_view(), name='generar_enlace_reset'),
]