"""
URL configuration for sistema_financiero project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls import handler404
from django.shortcuts import render
from stela import views as stela_views

urlpatterns = [
    # Redirect the root URL to 'stela/'
    path('', lambda request: redirect('stela/dashboard', permanent=False)),
    
    path("accounts/", include("accounts.urls")),
    path('accounts/', include('django.contrib.auth.urls')),
    path("stela/", include("stela.urls")),
    path('admin/', admin.site.urls),

# --- RUTAS DE API (PEGADAS AQUÍ) ---
    # Ahora las URL sí coincidirán con el JS
    path('api/get-ratios/', stela_views.get_ratios_api, name='api_get_ratios'),
    path('api/get-cuentas/', stela_views.get_cuentas_api, name='api_get_cuentas'),
    path('api/get-chart-data/', stela_views.get_chart_data_api, name='api_get_chart_data'),
    path('set-active-company/<str:empresa_nit>/', stela_views.set_active_company, name='set_active_company'),
]

# Pagina 404 aun no funciona porque estamos en debug
def custom404(request, exception):
    return render(request, '404.html', status=404)

handler404 = 'sistema_financiero.urls.custom404'