# Generated manually for catalog changes and ratio_tag addition

import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stela', '0001_initial'),
    ]

    operations = [
        # Cambiar Catalogo: primero eliminar unique_together, luego eliminar anio_catalogo, agregar fechas, cambiar a OneToOneField
        migrations.AlterUniqueTogether(
            name='catalogo',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='catalogo',
            name='anio_catalogo',
        ),
        migrations.AddField(
            model_name='catalogo',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='catalogo',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name='catalogo',
            options={'verbose_name': 'Catálogo', 'verbose_name_plural': 'Catálogos'},
        ),
        migrations.AlterField(
            model_name='catalogo',
            name='empresa',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='catalogo', to='stela.empresa'),
        ),
        
        # Actualizar GrupoCuenta: naturaleza ahora usa strings completos
        migrations.AlterField(
            model_name='grupocuenta',
            name='naturaleza',
            field=models.CharField(choices=[('Activo', 'Activo'), ('Pasivo', 'Pasivo'), ('Patrimonio', 'Patrimonio'), ('Ingreso', 'Ingreso'), ('Gasto', 'Gasto')], max_length=20),
        ),
        
        # Agregar campos a Cuenta: bg_bloque, er_bloque, ratio_tag
        migrations.AddField(
            model_name='cuenta',
            name='bg_bloque',
            field=models.CharField(blank=True, choices=[('', 'Sin bloque'), ('ACTIVO_CORRIENTE', 'Activo Corriente'), ('ACTIVO_NO_CORRIENTE', 'Activo No Corriente'), ('PASIVO_CORRIENTE', 'Pasivo Corriente'), ('PASIVO_NO_CORRIENTE', 'Pasivo No Corriente'), ('PATRIMONIO', 'Patrimonio')], default='', help_text='Bloque del Balance General donde se mostrará esta cuenta', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cuenta',
            name='er_bloque',
            field=models.CharField(blank=True, choices=[('', 'Sin bloque'), ('VENTAS_NETAS', 'Ventas Netas'), ('COSTO_NETO_VENTAS', 'Costo Neto de Ventas'), ('GASTOS_OPERATIVOS', 'Gastos Operativos'), ('OTROS_INGRESOS', 'Otros Ingresos'), ('OTROS_GASTOS', 'Otros Gastos'), ('GASTO_FINANCIERO', 'Gasto Financiero'), ('IMPUESTO_SOBRE_LA_RENTA', 'Impuesto sobre la Renta')], default='', help_text='Bloque del Estado de Resultados al que pertenece esta cuenta', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cuenta',
            name='ratio_tag',
            field=models.CharField(blank=True, choices=[('', 'Sin tag'), ('EFECTIVO', 'Efectivo (Caja + Bancos + Equivalentes)'), ('CUENTAS_POR_COBRAR', 'Cuentas por Cobrar'), ('INVENTARIOS', 'Inventarios'), ('ACTIVO_CORRIENTE', 'Activo Corriente'), ('ACTIVO_TOTAL', 'Activo Total'), ('ACTIVO_FIJO_NETO', 'Activo Fijo Neto'), ('PASIVO_CORRIENTE', 'Pasivo Corriente'), ('PASIVO_TOTAL', 'Pasivo Total'), ('PATRIMONIO_TOTAL', 'Patrimonio Total'), ('VENTAS_NETAS', 'Ventas Netas'), ('COSTO_VENTAS', 'Costo de Ventas'), ('COMPRAS', 'Compras'), ('GASTOS_OPERATIVOS', 'Gastos Operativos'), ('OTROS_INGRESOS', 'Otros Ingresos'), ('OTROS_GASTOS', 'Otros Gastos'), ('GASTO_FINANCIERO', 'Gasto Financiero'), ('IMPUESTO_RENTA', 'Impuesto sobre la Renta'), ('UTILIDAD_OPERATIVA', 'Utilidad Operativa (EBIT)'), ('UTILIDAD_NETA', 'Utilidad Neta'), ('DEPRECIACION', 'Depreciación'), ('AMORTIZACION', 'Amortización'), ('SERVICIO_DEUDA', 'Servicio de Deuda')], default='', help_text='Tag constante para cálculo de ratios. Múltiples cuentas pueden tener el mismo tag y se sumarán automáticamente.', max_length=50, null=True),
        ),
    ]

