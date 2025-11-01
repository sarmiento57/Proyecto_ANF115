from decimal import Decimal
from .estados import estado_dict

def analisis_vertical(empresa, periodo, tipo_estado):
    data = estado_dict(empresa, periodo, tipo_estado)
    base = next((v['monto'] for v in data.values() if v['base']), Decimal('0')) or Decimal('1')
    out = []
    for k,v in data.items():
        pct = (v['monto']/base)*Decimal('100')
        out.append({'clave':k,'nombre':v['nombre'],'monto':v['monto'],'porc':pct})
    return out

def analisis_horizontal(empresa, periodo_base, periodo_act, tipo_estado):
    a = estado_dict(empresa, periodo_base, tipo_estado)
    b = estado_dict(empresa, periodo_act,  tipo_estado)
    claves = set(a.keys()) | set(b.keys())
    out = []
    for k in sorted(claves):
        va = a.get(k, {'monto':Decimal('0'), 'nombre':k})
        vb = b.get(k, {'monto':Decimal('0'), 'nombre':k})
        vari = vb['monto'] - va['monto']
        porc = (vari/va['monto']*Decimal('100')) if va['monto'] else None
        out.append({'clave':k, 'nombre':va['nombre'] or vb['nombre'],
                    'base':va['monto'], 'actual':vb['monto'],
                    'variacion':vari, 'porc':porc})
    return out
