# stela/services/analisis.py
from decimal import Decimal, DivisionByZero
from stela.services.estados import estado_dict

def analisis_vertical(empresa, estado, anio, mes=None):
    data = estado_dict(empresa, estado, anio, mes)
    base = next((v["monto"] for v in data.values() if v["base"]), Decimal('0'))
    if not base:
        base = Decimal('1')  # evita crash; devuelve % relativos a 1 si no hay base
    out = []
    for k, v in data.items():
        porc = (v["monto"] / base) * Decimal('100')
        out.append({
            "clave": k, "nombre": v["nombre"],
            "monto": v["monto"], "porc": porc
        })
    # opcional: ordena por nombre o por clave
    return out

def analisis_horizontal(empresa, estado, anio_base, anio_act, mes=None):
    base = estado_dict(empresa, estado, anio_base, mes)
    act  = estado_dict(empresa, estado, anio_act,  mes)
    claves = set(base.keys()) | set(act.keys())
    out = []
    for k in sorted(claves):
        b = base.get(k, {"nombre":k, "monto":Decimal('0')})
        a = act.get(k,  {"nombre":k, "monto":Decimal('0')})
        vari = a["monto"] - b["monto"]
        porc = None
        if b["monto"]:
            try:
                porc = (vari / b["monto"]) * Decimal('100')
            except DivisionByZero:
                porc = None
        out.append({
            "clave": k, "nombre": a["nombre"] or b["nombre"],
            "base": b["monto"], "actual": a["monto"],
            "variacion": vari, "porc": porc
        })
    return out
