from django.contrib import admin
from .models import Ciuu, Empresa, Venta

# Catálogo
from stela.models.catalogo import Catalogo, GrupoCuenta, Cuenta
# Register your models here.
admin.site.register(Ciuu)
admin.site.register(Empresa)
admin.site.register(Venta)


@admin.register(Catalogo)
class CatalogoAdmin(admin.ModelAdmin):
    list_display = ("empresa", "anio_catalogo")
    list_filter = ("anio_catalogo", "empresa")

@admin.register(GrupoCuenta)
class GrupoCuentaAdmin(admin.ModelAdmin):
    list_display = ("catalogo", "nombre", "naturaleza")
    list_filter = ("naturaleza", "catalogo")
    search_fields = ("nombre",)

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("grupo", "codigo", "nombre", "aparece_en_balance")
    search_fields = ("codigo", "nombre")
    list_filter = ("grupo__catalogo__empresa", "grupo__catalogo__anio_catalogo", "grupo__naturaleza")

# Finanzas
from stela.models.finanzas import (
    Periodo, Balance, BalanceDetalle,
    LineaEstado, MapeoCuentaLinea,
    RatioDef, ResultadoRatio
)

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("empresa", "anio", "mes", "fecha_cerrado")
    list_filter = ("empresa", "anio", "mes")
    search_fields = ("empresa__razon_social", "empresa__nit")

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ("empresa", "periodo", "tipo_balance")
    list_filter = ("tipo_balance", "periodo__anio", "empresa")

@admin.register(BalanceDetalle)
class BalanceDetalleAdmin(admin.ModelAdmin):
    list_display = ("balance", "cuenta", "debe", "haber", "saldo")
    search_fields = ("cuenta__codigo", "cuenta__nombre")
    list_filter = ("balance__tipo_balance", "balance__periodo__anio")

@admin.register(LineaEstado)
class LineaEstadoAdmin(admin.ModelAdmin):
    list_display = ("estado", "clave", "nombre", "base_vertical")
    list_filter = ("estado", "base_vertical")
    search_fields = ("clave", "nombre")

@admin.register(MapeoCuentaLinea)
class MapeoCuentaLineaAdmin(admin.ModelAdmin):
    list_display = ("linea", "cuenta", "signo")
    search_fields = ("linea__clave", "linea__nombre", "cuenta__codigo", "cuenta__nombre")
    list_filter = ("linea__estado",)

@admin.register(RatioDef)
class RatioDefAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "porcentaje")
    search_fields = ("clave", "nombre")

@admin.register(ResultadoRatio)
class ResultadoRatioAdmin(admin.ModelAdmin):
    list_display = ("empresa", "periodo", "ratio", "valor")
    list_filter = ("periodo__anio", "ratio")
    search_fields = ("empresa__razon_social", "empresa__nit")
