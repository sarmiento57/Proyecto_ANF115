from django.db import models
from .empresa import Empresa

class Catalogo(models.Model):
    id_catalogo = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='catalogos')
    anio_catalogo = models.IntegerField()

    class Meta:
        unique_together = ('empresa', 'anio_catalogo')

    def __str__(self):
        return f"Catálogo {self.empresa.nit} - {self.anio_catalogo}"

class GrupoCuenta(models.Model):
    NAT_CHOICES = [('A','Activo'), ('L','Pasivo'), ('P','Patrimonio'),
                   ('I','Ingreso'), ('G','Gasto')]
    id_grupoCuenta = models.AutoField(primary_key=True)
    catalogo = models.ForeignKey(Catalogo, on_delete=models.CASCADE, related_name='grupos')
    nombre = models.CharField(max_length=120)
    naturaleza = models.CharField(max_length=1, choices=NAT_CHOICES)

    def __str__(self):
        return f"{self.nombre} ({self.get_naturaleza_display()})"

class Cuenta(models.Model):
    id_cuenta = models.AutoField(primary_key=True)
    grupo = models.ForeignKey(GrupoCuenta, on_delete=models.CASCADE, related_name='cuentas')
    codigo = models.CharField(max_length=30)             # 1101, 41-01, etc.
    nombre = models.CharField(max_length=180)
    aparece_en_balance = models.BooleanField(default=True)

    class Meta:
        unique_together = ('grupo', 'codigo')

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
