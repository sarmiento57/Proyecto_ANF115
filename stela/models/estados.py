# stela/models/estados.py
from django.db import models
from .empresa import Empresa

class EstadoValor(models.Model):
    """
    Repositorio simple de valores de estados (BAL/RES) por línea/claves.
    Así puedes cargar balances/ER anuales o mensuales mientras no tengas catálogo.
    """
    ESTADOS = [('BAL','Balance'), ('RES','Resultados')]
    empresa   = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    estado    = models.CharField(max_length=3, choices=ESTADOS)
    clave     = models.CharField(max_length=64)   # p.ej. TOTAL_ACTIVO, VENTAS_NETAS
    nombre    = models.CharField(max_length=255)  # etiqueta amigable
    anio      = models.IntegerField()
    mes       = models.IntegerField(null=True, blank=True)  # opcional si lo usas mensual
    monto     = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=['empresa','estado','anio','mes','clave']),
        ]
        unique_together = ('empresa','estado','anio','mes','clave')

class LineaEstado(models.Model):
    """
    Plantilla de líneas por estado, y cuál es la base para análisis vertical.
    Si no quieres personalizar por empresa aún, mantenla global.
    """
    ESTADOS = [('BAL','Balance'), ('RES','Resultados')]
    estado        = models.CharField(max_length=3, choices=ESTADOS)
    clave         = models.CharField(max_length=64, unique=True)
    nombre        = models.CharField(max_length=255)
    base_vertical = models.BooleanField(default=False)  # ej: TOTAL_ACTIVO o VENTAS_NETAS

class RatioDef(models.Model):
    """
    Fórmulas declarativas sobre claves de LineaEstado (o EstadoValor).
    """
    clave      = models.CharField(max_length=64, unique=True)      # LIQUIDEZ_CORRIENTE
    nombre     = models.CharField(max_length=255)                   # Liquidez corriente
    formula    = models.TextField()                                 # (ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)
    porcentaje = models.BooleanField(default=False)                 # multiplicar por 100
