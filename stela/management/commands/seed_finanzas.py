from django.core.management.base import BaseCommand
from stela.models.finanzas import LineaEstado, RatioDef

LINEAS = [
  ('BAL','TOTAL_ACTIVO','Total Activo', True),
  ('BAL','ACTIVO_CORRIENTE','Activo Corriente', False),
  ('BAL','PASIVO_CORRIENTE','Pasivo Corriente', False),
  ('BAL','PATRIMONIO_TOTAL','Patrimonio', False),

  ('RES','VENTAS_NETAS','Ventas Netas', True),
  ('RES','COSTO_VENTAS','Costo de Ventas', False),
  ('RES','UTILIDAD_NETA','Utilidad Neta', False),
]

RATIOS = [
  ('LIQUIDEZ_CORRIENTE','Liquidez Corriente','(ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)', False),
  ('ENDEUDAMIENTO','Endeudamiento','(PASIVO_CORRIENTE)/(TOTAL_ACTIVO)', True),
  ('MARGEN_NETO','Margen Neto','(UTILIDAD_NETA)/(VENTAS_NETAS)', True),
]

class Command(BaseCommand):
    help = "Crea líneas de estado y ratios base"

    def handle(self, *args, **kwargs):
        for e,c,n,b in LINEAS:
            LineaEstado.objects.get_or_create(
                estado=e, clave=c,
                defaults={'nombre': n, 'base_vertical': b}
            )
        for c,n,f,p in RATIOS:
            RatioDef.objects.get_or_create(
                clave=c,
                defaults={'nombre': n, 'formula': f, 'porcentaje': p}
            )
        self.stdout.write(self.style.SUCCESS("✅ Líneas y ratios base creados"))
