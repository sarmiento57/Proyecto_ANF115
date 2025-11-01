# stela/services/estados.py
from decimal import Decimal
from collections import defaultdict
from stela.models.estados import EstadoValor, LineaEstado

def estado_dict(empresa, estado, anio, mes=None):
    """
    Retorna: {clave: {"nombre":..., "monto": Decimal, "base":bool}}
    Suma duplicados si los hay.
    """
    qs = EstadoValor.objects.filter(empresa=empresa, estado=estado, anio=anio)
    if mes is not None:
        qs = qs.filter(mes=mes)
    data = defaultdict(lambda: {"nombre":"", "monto": Decimal('0'), "base": False})
    bases = {le.clave for le in LineaEstado.objects.filter(estado=estado, base_vertical=True)}
    nombres = {le.clave: le.nombre for le in LineaEstado.objects.filter(estado=estado)}

    for row in qs:
        k = row.clave
        data[k]["nombre"] = row.nombre or nombres.get(k, k)
        data[k]["monto"]  += Decimal(row.monto)
        data[k]["base"]    = k in bases
    # si plantilla tiene claves sin datos, incluirlas en 0 (opcional)
    for le in LineaEstado.objects.filter(estado=estado):
        data.setdefault(le.clave, {"nombre": le.nombre, "monto": Decimal('0'), "base": le.base_vertical})
    return dict(data)
