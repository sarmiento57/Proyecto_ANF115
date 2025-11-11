"""
Servicio para mapeo automático de cuentas del catálogo a líneas de estado.

Este módulo automatiza el mapeo de cuentas a líneas de estado basándose en el
campo ratio_tag de cada cuenta.

Flujo de cálculo de ratios:
BalanceDetalle → MapeoCuentaLinea → LineaEstado → RatioDef → ResultadoRatio

Las cuentas se mapean automáticamente según su ratio_tag:
- ratio_tag='ACTIVO_CORRIENTE' → LineaEstado.clave='ACTIVO_CORRIENTE'
- ratio_tag='VENTAS_NETAS' → LineaEstado.clave='VENTAS_NETAS'
- Múltiples cuentas con el mismo ratio_tag se mapean a la misma LineaEstado

IMPORTANTE: El mapeo se basa en ratio_tag, no en bg_bloque o er_bloque.
Esto permite que múltiples cuentas (ej: Caja, Bancos, Equivalentes) con el mismo
ratio_tag se agrupen automáticamente en la misma línea de estado.
"""

from stela.models.finanzas import LineaEstado, MapeoCuentaLinea
from stela.models.catalogo import Cuenta
from collections import defaultdict


def mapear_cuentas_por_bloques(catalogo):
    """
    Mapea automáticamente las cuentas del catálogo a líneas de estado
    basándose en el campo ratio_tag de cada cuenta.
    
    Múltiples cuentas pueden tener el mismo ratio_tag y todas se mapean
    a la misma LineaEstado. Por ejemplo:
    - Caja (ratio_tag='EFECTIVO')
    - Bancos (ratio_tag='EFECTIVO')
    - Equivalentes (ratio_tag='EFECTIVO')
    Todas se mapean a la misma línea si existe LineaEstado.clave='EFECTIVO'
    
    Args:
        catalogo: Instancia de Catalogo
        
    Raises:
        ValueError: Si faltan líneas de estado requeridas en la base de datos
        
    Returns:
        dict: Resumen de mapeos creados con claves de líneas y cantidad de cuentas mapeadas
    """
    # Líneas de estado requeridas para los ratios principales
    lineas_requeridas = [
        'TOTAL_ACTIVO',
        'ACTIVO_CORRIENTE',
        'PASIVO_CORRIENTE',
        'VENTAS_NETAS',
        'UTILIDAD_NETA'  # Se calcula, no se mapea directamente
    ]
    
    # Verificar que todas las líneas requeridas existan
    lineas_faltantes = []
    for clave in lineas_requeridas:
        if not LineaEstado.objects.filter(clave=clave).exists():
            lineas_faltantes.append(clave)
    
    if lineas_faltantes:
        raise ValueError(
            f"Faltan líneas de estado requeridas: {', '.join(lineas_faltantes)}. "
            f"Ejecuta: python manage.py seed_finanzas"
        )
    
    resumen = defaultdict(int)
    
    # Obtener todas las cuentas del catálogo que tengan ratio_tag
    cuentas_con_tag = Cuenta.objects.filter(
        grupo__catalogo=catalogo,
        ratio_tag__isnull=False
    ).exclude(ratio_tag='')
    
    # Agrupar cuentas por ratio_tag
    cuentas_por_tag = defaultdict(list)
    for cuenta in cuentas_con_tag:
        tag = cuenta.ratio_tag.strip()
        if tag:
            # Manejar tags negativos (ej: -VENTAS_NETAS para restar)
            signo = -1 if tag.startswith('-') else 1
            tag_limpio = tag.lstrip('-')
            cuentas_por_tag[tag_limpio].append((cuenta, signo))
    
    # Mapear cada grupo de cuentas a su línea de estado correspondiente
    for ratio_tag, lista_cuentas in cuentas_por_tag.items():
        try:
            # Buscar la línea de estado con clave igual al ratio_tag
            linea = LineaEstado.objects.get(clave=ratio_tag)
        except LineaEstado.DoesNotExist:
            # Si no existe la línea, continuar (puede ser un tag que no se usa en ratios)
            continue
        
        # Eliminar mapeos existentes para esta línea en este catálogo
        # Esto permite re-mapear sin crear duplicados
        MapeoCuentaLinea.objects.filter(
            linea=linea,
            cuenta__grupo__catalogo=catalogo
        ).delete()
        
        # Crear nuevos mapeos para todas las cuentas con este tag
        cuentas_mapeadas = 0
        for cuenta, signo in lista_cuentas:
            mapeo, created = MapeoCuentaLinea.objects.get_or_create(
                cuenta=cuenta,
                linea=linea,
                defaults={'signo': signo}
            )
            if created:
                cuentas_mapeadas += 1
            elif mapeo.signo != signo:
                # Actualizar signo si cambió
                mapeo.signo = signo
                mapeo.save()
                cuentas_mapeadas += 1
        
        resumen[ratio_tag] = cuentas_mapeadas
    
    # Mapear TOTAL_ACTIVO (suma de todas las cuentas de activo)
    # Esto es especial porque no se mapea por ratio_tag, sino por naturaleza
    try:
        linea_total_activo = LineaEstado.objects.get(clave='TOTAL_ACTIVO')
    except LineaEstado.DoesNotExist:
        pass
    else:
        # Obtener todas las cuentas de activo (corriente y no corriente)
        # que no tengan un ratio_tag específico que ya las mapee
        cuentas_activo = Cuenta.objects.filter(
            grupo__catalogo=catalogo,
            grupo__naturaleza='Activo',
            bg_bloque__in=['ACTIVO_CORRIENTE', 'ACTIVO_NO_CORRIENTE']
        )
        
        # Eliminar mapeos existentes
        MapeoCuentaLinea.objects.filter(
            linea=linea_total_activo,
            cuenta__grupo__catalogo=catalogo
        ).delete()
        
        # Crear nuevos mapeos (solo si la cuenta no está ya mapeada por ratio_tag)
        cuentas_mapeadas = 0
        for cuenta in cuentas_activo:
            # Verificar si la cuenta ya está mapeada por ratio_tag
            # Si tiene ratio_tag='ACTIVO_CORRIENTE' o similar, ya está mapeada
            if cuenta.ratio_tag and cuenta.ratio_tag.strip() in ['ACTIVO_CORRIENTE', 'ACTIVO_TOTAL', 'ACTIVO_FIJO_NETO']:
                continue
            
            mapeo, created = MapeoCuentaLinea.objects.get_or_create(
                cuenta=cuenta,
                linea=linea_total_activo,
                defaults={'signo': 1}
            )
            if created:
                cuentas_mapeadas += 1
        
        resumen['TOTAL_ACTIVO'] = cuentas_mapeadas
    
    # NOTA: UTILIDAD_NETA no se mapea directamente desde cuentas.
    # Se calcula en calcular_totales_por_seccion() a partir de los bloques
    # del Estado de Resultados (VENTAS_NETAS, COSTO_NETO_VENTAS, etc.)
    
    return dict(resumen)

