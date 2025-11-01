from django.db import models
from decimal import Decimal
from .empresa import Empresa
from .catalogo import Cuenta

class Periodo(models.Model):
    id_periodo = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='periodos')
    # Puedes usar mensual o anual. Aquí: año y opcional mes.
    anio = models.IntegerField()
    mes = models.IntegerField(null=True, blank=True)
    fecha_cerrado = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('empresa','anio','mes')

    def __str__(self):
        suf = f"-{self.mes:02d}" if self.mes else ""
        return f"{self.empresa.nit} {self.anio}{suf}"

class Balance(models.Model):
    TIPO = [('BAL','Balance'), ('RES','Resultados')]
    id_balance = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    tipo_balance = models.CharField(max_length=3, choices=TIPO)

    class Meta:
        unique_together = ('empresa','periodo','tipo_balance')

    def __str__(self):
        return f"{self.empresa.nit} {self.periodo} {self.tipo_balance}"

class BalanceDetalle(models.Model):
    balance = models.ForeignKey(Balance, on_delete=models.CASCADE, related_name='detalles')
    cuenta  = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    debe    = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    haber   = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    saldo   = models.DecimalField(max_digits=18, decimal_places=2, default=0)  # calculado

class LineaEstado(models.Model):
    ESTADO = [('BAL','Balance'), ('RES','Resultados')]
    estado = models.CharField(max_length=3, choices=ESTADO)
    clave = models.CharField(max_length=64, unique=True)             # TOTAL_ACTIVO, VENTAS_NETAS...
    nombre = models.CharField(max_length=255)
    base_vertical = models.BooleanField(default=False)               # p.ej. TOTAL_ACTIVO / VENTAS_NETAS

    def __str__(self):
        return f"{self.estado}:{self.clave}"

class MapeoCuentaLinea(models.Model):
    """Asigna cuentas del catálogo a líneas (con signo)."""
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    linea  = models.ForeignKey(LineaEstado, on_delete=models.CASCADE)
    signo  = models.SmallIntegerField(default=1)

    class Meta:
        unique_together = ('cuenta','linea')

class RatioDef(models.Model):
    clave = models.CharField(max_length=64, unique=True)             # LIQUIDEZ_CORRIENTE
    nombre = models.CharField(max_length=255)
    formula = models.TextField()                                     # (ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)
    porcentaje = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

class ResultadoRatio(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    ratio   = models.ForeignKey(RatioDef, on_delete=models.CASCADE)
    valor   = models.DecimalField(max_digits=18, decimal_places=4, null=True)

    class Meta:
        unique_together = ('empresa','periodo','ratio')
