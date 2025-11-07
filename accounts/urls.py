from django.urls import path

from .views import register, perfil_view, perfil_edit

urlpatterns = [
    path("register/", register, name="register"),
    path("perfil/", perfil_view, name="perfil_view"),
    path("perfil/editar/", perfil_edit, name="perfil_edit"),
]