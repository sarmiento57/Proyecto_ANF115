from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("crear-empresa/", views.crearEmpresa, name="crear_empresa"),
    path("tools/",views.tools,name="tools"),
]