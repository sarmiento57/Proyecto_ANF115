from decimal import Decimal
from django.db.models import Sum
from stela.models.finanzas import Balance, BalanceDetalle, LineaEstado, MapeoCuentaLinea

def recalcular_saldos_detalle(balance: Balance):
    """Si importas debe/haber, calcula saldo según naturaleza del grupo."""
    detalles = BalanceDetalle.objects.filter(balance=balance).select_related('cuenta__grupo')
    bulk = []
    for d in detalles:
        nat = d.cuenta.grupo.naturaleza
        if nat in ('A','G'):
            d.saldo = (d.debe or 0) - (d.haber or 0)
        else:
            d.saldo = (d.haber or 0) - (d.debe or 0)
        bulk.append(d)
    BalanceDetalle.objects.bulk_update(bulk, ['saldo'])

def estado_dict(empresa, periodo, tipo_estado):
    """
    Devuelve {clave: {'nombre', 'monto', 'base'}}
    suma los saldos de las cuentas mapeadas a cada línea.
    """
    bal = Balance.objects.get(empresa=empresa, periodo=periodo, tipo_balance=tipo_estado)
    # Pre-indexar detalle por cuenta para velocidad
    detalles = BalanceDetalle.objects.filter(balance=bal).select_related('cuenta')
    by_cuenta = {d.cuenta_id: d for d in detalles}
    data = {}
    for le in LineaEstado.objects.filter(estado=tipo_estado):
        total = Decimal('0')
        for map_ in MapeoCuentaLinea.objects.filter(linea=le).only('cuenta_id','signo'):
            det = by_cuenta.get(map_.cuenta_id)
            if not det:
                continue
            total += (det.saldo or 0) * map_.signo
        data[le.clave] = {'nombre': le.nombre, 'monto': total, 'base': le.base_vertical}
    return data
