from django.db import models
from .empresa import Empresa

class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, max_length=4)
    mes_venta = models.DateField()
    saldo_venta = models.FloatField()
    anio = models.IntegerField()
    proyeccion = models.BooleanField()

    def __str__(self):
        return f"Venta {self.id_venta}"