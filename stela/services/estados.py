from decimal import Decimal
from django.db.models import Sum, Q
from stela.models.finanzas import Balance, BalanceDetalle, LineaEstado, MapeoCuentaLinea
from stela.models.catalogo import Cuenta

def recalcular_saldos_detalle(balance: Balance):
    """Si importas debe/haber, calcula saldo según naturaleza del grupo."""
    detalles = BalanceDetalle.objects.filter(balance=balance).select_related('cuenta__grupo')
    bulk = []
    for d in detalles:
        nat = d.cuenta.grupo.naturaleza
        if nat in ('Activo', 'Gasto'):
            d.saldo = (d.debe or 0) - (d.haber or 0)
        else:
            d.saldo = (d.haber or 0) - (d.debe or 0)
        bulk.append(d)
    BalanceDetalle.objects.bulk_update(bulk, ['saldo'])

def calcular_totales_por_seccion(balance: Balance):
    """
    Calcula los totales por sección del Estado de Resultados.
    Devuelve un diccionario con los totales de cada sección.
    Si no hay cuentas para un bloque, el subtotal será 0.
    """
    detalles = BalanceDetalle.objects.filter(balance=balance).select_related('cuenta__grupo')
    
    # Agrupar por sección
    totales_seccion = {}
    
    for detalle in detalles:
        cuenta = detalle.cuenta
        # Solo procesar cuentas de Ingreso o Gasto con bloque ER asignado
        if cuenta.grupo.naturaleza in ('Ingreso', 'Gasto') and cuenta.er_bloque:
            bloque = cuenta.er_bloque
            if bloque not in totales_seccion:
                totales_seccion[bloque] = Decimal('0')
            
            # Para ingresos: sumar saldo positivo, para gastos: sumar saldo negativo
            if cuenta.grupo.naturaleza == 'Ingreso':
                totales_seccion[bloque] += detalle.saldo or Decimal('0')
            else:  # Gasto
                totales_seccion[bloque] -= detalle.saldo or Decimal('0')
    
    # Inicializar todos los bloques posibles con 0 si no tienen cuentas
    bloques_posibles = [
        'VENTAS_NETAS',
        'COSTO_NETO_VENTAS',
        'GASTOS_OPERATIVOS',
        'OTROS_INGRESOS',
        'OTROS_GASTOS',
        'GASTO_FINANCIERO',
        'IMPUESTO_SOBRE_LA_RENTA'
    ]
    
    for bloque in bloques_posibles:
        if bloque not in totales_seccion:
            totales_seccion[bloque] = Decimal('0')
    
    # Calcular secciones derivadas (que dependen de otras secciones)
    secciones_calculadas = {}
    
    # Utilidad Bruta = Ventas Netas - Costo Neto de Ventas
    # Si no hay cuentas, ambos serán 0, así que el resultado será 0
    secciones_calculadas['UTILIDAD_BRUTA'] = (
        totales_seccion.get('VENTAS_NETAS', Decimal('0')) - 
        totales_seccion.get('COSTO_NETO_VENTAS', Decimal('0'))
    )
    
    # Utilidad Operativa = Utilidad Bruta - Gastos Operativos
    utilidad_bruta = secciones_calculadas.get('UTILIDAD_BRUTA', Decimal('0'))
    secciones_calculadas['UTILIDAD_OPERATIVA'] = (
        utilidad_bruta - 
        totales_seccion.get('GASTOS_OPERATIVOS', Decimal('0'))
    )
    
    # Utilidad Neta = Utilidad Operativa - Gasto Financiero + Otros Ingresos - Otros Gastos
    utilidad_operativa = secciones_calculadas.get('UTILIDAD_OPERATIVA', Decimal('0'))
    secciones_calculadas['UTILIDAD_NETA'] = (
        utilidad_operativa -
        totales_seccion.get('GASTO_FINANCIERO', Decimal('0')) +
        totales_seccion.get('OTROS_INGRESOS', Decimal('0')) -
        totales_seccion.get('OTROS_GASTOS', Decimal('0'))
    )
    
    # Combinar totales directos y calculados
    totales_finales = {**totales_seccion, **secciones_calculadas}
    
    return totales_finales


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
