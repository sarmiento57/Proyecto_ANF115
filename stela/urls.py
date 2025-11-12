from django.urls import path
from django.contrib.auth import views as auth_views


from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/empresa/<str:empresa_nit>/", views.empresa_detalles, name="empresa_detalles"),
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
    
    # URLs para Catálogo de Cuentas
    path("catalogo/upload/", views.catalogo_upload_csv, name="catalogo_upload"),
    path("catalogo/create/", views.catalogo_create_manual, name="catalogo_create_manual"),
    path("catalogo/mapeo/<int:catalogo_id>/", views.catalogo_mapeo_cuentas, name="catalogo_mapeo"),
    
    # URLs para eliminar estados financieros
    path("balance/eliminar/<int:balance_id>/", views.eliminar_balance, name="eliminar_balance"),
    
    # URLs para descargar plantillas
    path("catalogo/plantilla/csv/", views.descargar_plantilla_catalogo_csv, name="descargar_plantilla_catalogo_csv"),
    path("catalogo/plantilla/excel/", views.descargar_plantilla_catalogo_excel, name="descargar_plantilla_catalogo_excel"),
    path("catalogo/plantilla/estados/csv/", views.descargar_plantilla_estados_csv, name="descargar_plantilla_estados_csv"),
    path("catalogo/plantilla/estados/excel/<int:catalogo_id>/", views.descargar_plantilla_estados_excel, name="descargar_plantilla_estados_excel"),

    # logout de usuario
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

# --- RUTAS DE API PARA LOS GRÁFICOS ---
    path('api/get-ratios/', views.get_ratios_api, name='api_get_ratios'),
    path('api/get-cuentas/', views.get_cuentas_api, name='api_get_cuentas'),

    path('api/get-chart-data/', views.get_chart_data_api, name='api_get_chart_data'),
    path('set-active-company/<str:empresa_nit>/', views.set_active_company, name='set_active_company'),
    path('api/get-periodos/', views.get_periodos_api, name='api_get_periodos'),
]