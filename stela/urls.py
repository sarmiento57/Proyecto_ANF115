from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("crear-empresa/", views.crearEmpresa, name="crear_empresa"),
    path("editar-empresa/<str:nit>/", views.editarEmpresa, name="editar_empresa"),
    path("tools/",views.tools,name="tools"),
    path("tools/finanzas/", views.tools_finanzas, name="tools_finanzas"),
    path("projections/",views.projections,name="projections"),
    
    # URLs para CRUD de CIIU (Catálogos)
    path("catalogo/ciiu/", views.ciiu_list, name="ciiu_list"),
    path("catalogo/ciiu/crear/", views.ciiu_create, name="ciiu_create"),
    path("catalogo/ciiu/<str:codigo>/editar/", views.ciiu_update, name="ciiu_update"),
    path("catalogo/ciiu/<str:codigo>/eliminar/", views.ciiu_delete, name="ciiu_delete"),
]