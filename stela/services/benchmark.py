from decimal import Decimal
from statistics import mean, pstdev
from stela.models.finanzas import ResultadoRatio, RatioDef

def benchmarking_por_ciiu(ciiu, periodo):
    ratios = RatioDef.objects.all()
    empresas_ids = list(ciiu.empresa_set.values_list('pk', flat=True))
    out = {}
    for r in ratios:
        vals = list(ResultadoRatio.objects
                    .filter(periodo=periodo, ratio=r, empresa_id__in=empresas_ids)
                    .values_list('valor', flat=True))
        vals = [Decimal(v) for v in vals if v is not None]
        if not vals:
            continue
        prom = Decimal(mean(vals))
        desv = Decimal(pstdev(vals)) if len(vals) > 1 else Decimal('0')
        out[r.clave] = {'nombre': r.nombre, 'promedio': prom, 'desv': desv}
    return out

def etiqueta_semaforo(valor, prom, desv, k=1):
    if valor is None: return 'NA'
    if desv == 0:
        return 'OK' if valor == prom else ('ALTO' if valor > prom else 'BAJO')
    if valor > prom + k*desv: return 'ALTO'
    if valor < prom - k*desv: return 'BAJO'
    return 'OK'
