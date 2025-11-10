from django.db import models
from .empresa import Empresa

class Catalogo(models.Model):
    id_catalogo = models.AutoField(primary_key=True)
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='catalogo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catálogo'
        verbose_name_plural = 'Catálogos'

    def __str__(self):
        return f"Catálogo {self.empresa.razon_social}"

class GrupoCuenta(models.Model):
    NAT_CHOICES = [
        ('Activo', 'Activo'),
        ('Pasivo', 'Pasivo'),
        ('Patrimonio', 'Patrimonio'),
        ('Ingreso', 'Ingreso'),
        ('Gasto', 'Gasto')
    ]
    id_grupoCuenta = models.AutoField(primary_key=True)
    catalogo = models.ForeignKey(Catalogo, on_delete=models.CASCADE, related_name='grupos')
    nombre = models.CharField(max_length=120)
    naturaleza = models.CharField(max_length=20, choices=NAT_CHOICES)

    def __str__(self):
        return f"{self.nombre} ({self.get_naturaleza_display()})"

class Cuenta(models.Model):
    # Bloques del Estado de Resultados
    ER_BLOQUES = [
        ('', 'Sin bloque'),
        ('VENTAS_NETAS', 'Ventas Netas'),
        ('COSTO_NETO_VENTAS', 'Costo Neto de Ventas'),
        ('GASTOS_OPERATIVOS', 'Gastos Operativos'),
        ('OTROS_INGRESOS', 'Otros Ingresos'),
        ('OTROS_GASTOS', 'Otros Gastos'),
        ('GASTO_FINANCIERO', 'Gasto Financiero'),
        ('IMPUESTO_SOBRE_LA_RENTA', 'Impuesto sobre la Renta'),
    ]
    
    # Bloques del Balance General
    BG_BLOQUES = [
        ('', 'Sin bloque'),
        ('ACTIVO_CORRIENTE', 'Activo Corriente'),
        ('ACTIVO_NO_CORRIENTE', 'Activo No Corriente'),
        ('PASIVO_CORRIENTE', 'Pasivo Corriente'),
        ('PASIVO_NO_CORRIENTE', 'Pasivo No Corriente'),
        ('PATRIMONIO', 'Patrimonio'),
    ]
    
    # Tags para ratios (nombres constantes que apuntan a valores para cálculo de ratios)
    RATIO_TAGS = [
        ('', 'Sin tag'),
        ('EFECTIVO', 'Efectivo (Caja + Bancos + Equivalentes)'),
        ('CUENTAS_POR_COBRAR', 'Cuentas por Cobrar'),
        ('INVENTARIOS', 'Inventarios'),
        ('ACTIVO_CORRIENTE', 'Activo Corriente'),
        ('ACTIVO_TOTAL', 'Activo Total'),
        ('ACTIVO_FIJO_NETO', 'Activo Fijo Neto'),
        ('PASIVO_CORRIENTE', 'Pasivo Corriente'),
        ('PASIVO_TOTAL', 'Pasivo Total'),
        ('PATRIMONIO_TOTAL', 'Patrimonio Total'),
        ('VENTAS_NETAS', 'Ventas Netas'),
        ('COSTO_VENTAS', 'Costo de Ventas'),
        ('COMPRAS', 'Compras'),
        ('GASTOS_OPERATIVOS', 'Gastos Operativos'),
        ('OTROS_INGRESOS', 'Otros Ingresos'),
        ('OTROS_GASTOS', 'Otros Gastos'),
        ('GASTO_FINANCIERO', 'Gasto Financiero'),
        ('IMPUESTO_RENTA', 'Impuesto sobre la Renta'),
        ('UTILIDAD_OPERATIVA', 'Utilidad Operativa (EBIT)'),
        ('UTILIDAD_NETA', 'Utilidad Neta'),
        ('DEPRECIACION', 'Depreciación'),
        ('AMORTIZACION', 'Amortización'),
        ('SERVICIO_DEUDA', 'Servicio de Deuda'),
    ]
    
    id_cuenta = models.AutoField(primary_key=True)
    grupo = models.ForeignKey(GrupoCuenta, on_delete=models.CASCADE, related_name='cuentas')
    codigo = models.CharField(max_length=30)             # 1101, 41-01, etc.
    nombre = models.CharField(max_length=180)
    aparece_en_balance = models.BooleanField(default=True)
    er_bloque = models.CharField(
        max_length=50, 
        choices=ER_BLOQUES, 
        default='',
        blank=True,
        null=True,
        help_text='Bloque del Estado de Resultados al que pertenece esta cuenta'
    )
    bg_bloque = models.CharField(
        max_length=50,
        choices=BG_BLOQUES,
        default='',
        blank=True,
        null=True,
        help_text='Bloque del Balance General donde se mostrará esta cuenta'
    )
    ratio_tag = models.CharField(
        max_length=50,
        choices=RATIO_TAGS,
        default='',
        blank=True,
        null=True,
        help_text='Tag constante para cálculo de ratios. Múltiples cuentas pueden tener el mismo tag y se sumarán automáticamente.'
    )

    class Meta:
        unique_together = ('grupo', 'codigo')

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
