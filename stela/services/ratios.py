import ast, operator, re
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from stela.models.finanzas import RatioDef, ResultadoRatio, Balance, BalanceDetalle
from stela.models.catalogo import Cuenta
from .estados import estado_dict, calcular_totales_por_seccion

# Operadores permitidos en las fórmulas
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

def _eval(node):
    """Evalúa un AST con operaciones seguras (solo +, -, *, / y unarios)."""
    if isinstance(node, ast.Num):  # números literales
        return Decimal(str(node.n))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand)
    if isinstance(node, ast.BinOp):
        return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("Expresión no soportada")

def _replace_missing(expr: str) -> str:
    """
    Si en la fórmula aparecen CLAVES que no están en cache,
    las reemplazamos por (0) para evitar NameError.
    """
    return re.sub(r'\b[A-Z_][A-Z0-9_]*\b', '(0)', expr)


def calcular_valores_desde_ratio_tag(empresa, periodo, tipo_estado='BAL'):
    """
    Calcula los valores de las líneas de estado directamente desde las cuentas
    usando ratio_tag y bg_bloque/er_bloque, sin depender de MapeoCuentaLinea.
    
    Para cada ratio_tag, suma los saldos de todas las cuentas que tienen ese tag.
    También agrega valores por bg_bloque y er_bloque para compatibilidad.
    
    Args:
        empresa: Instancia de Empresa
        periodo: Instancia de Periodo
        tipo_estado: 'BAL' o 'RES'
        
    Returns:
        dict: {clave: Decimal} con los valores calculados
    """
    try:
        balance = Balance.objects.get(empresa=empresa, periodo=periodo, tipo_balance=tipo_estado)
    except Balance.DoesNotExist:
        return {}
    
    # Obtener todos los detalles del balance con sus cuentas
    detalles = BalanceDetalle.objects.filter(
        balance=balance
    ).select_related('cuenta', 'cuenta__grupo')
    
    # Agrupar por ratio_tag y sumar saldos
    valores_por_tag = {}
    valores_por_bloque = {}
    
    for detalle in detalles:
        cuenta = detalle.cuenta
        saldo = detalle.saldo or Decimal('0')
        
        # Si la cuenta tiene ratio_tag, agregar su saldo
        if cuenta.ratio_tag and cuenta.ratio_tag.strip():
            tag = cuenta.ratio_tag.strip()
            # Manejar tags negativos (ej: -VENTAS_NETAS)
            signo = -1 if tag.startswith('-') else 1
            tag_limpio = tag.lstrip('-')
            
            if tag_limpio not in valores_por_tag:
                valores_por_tag[tag_limpio] = Decimal('0')
            
            valores_por_tag[tag_limpio] += saldo * signo
        
        # También agregar por bloques para compatibilidad
        # Para Balance General: sumar saldos por bg_bloque
        if tipo_estado == 'BAL' and cuenta.bg_bloque:
            bloque = cuenta.bg_bloque.strip()
            if bloque:
                if bloque not in valores_por_bloque:
                    valores_por_bloque[bloque] = Decimal('0')
                # Sumar el saldo directamente (ya está calculado correctamente según naturaleza)
                valores_por_bloque[bloque] += saldo
        
        # Para Estado de Resultados: sumar saldos por er_bloque
        if tipo_estado == 'RES' and cuenta.er_bloque:
            bloque = cuenta.er_bloque.strip()
            if bloque:
                if bloque not in valores_por_bloque:
                    valores_por_bloque[bloque] = Decimal('0')
                valores_por_bloque[bloque] += saldo
    
    # Mapear bloques a claves de ratio (para compatibilidad con fórmulas)
    mapeo_bloques = {
        'ACTIVO_CORRIENTE': 'ACTIVO_CORRIENTE',
        'PASIVO_CORRIENTE': 'PASIVO_CORRIENTE',
        'PATRIMONIO': 'PATRIMONIO_TOTAL',
        'VENTAS_NETAS': 'VENTAS_NETAS',
    }
    
    # Siempre usar valores de bloques si existen (tienen prioridad sobre ratio_tag individual)
    # Esto asegura que se calculen correctamente desde bg_bloque/er_bloque
    for bloque, clave in mapeo_bloques.items():
        if bloque in valores_por_bloque:
            valores_por_tag[clave] = valores_por_bloque[bloque]
    
    # Para UTILIDAD_NETA, calcular desde los bloques consolidados
    if tipo_estado == 'RES':
        totales = calcular_totales_por_seccion(balance)
        if 'UTILIDAD_NETA' in totales:
            valores_por_tag['UTILIDAD_NETA'] = totales['UTILIDAD_NETA']
    
    # Para Balance General, calcular valores agregados siempre
    if tipo_estado == 'BAL':
        # TOTAL_ACTIVO: sumar todos los activos
        total_activo = Decimal('0')
        for detalle in detalles:
            if detalle.cuenta.grupo.naturaleza == 'Activo':
                total_activo += detalle.saldo or Decimal('0')
        valores_por_tag['TOTAL_ACTIVO'] = total_activo
        
        # ACTIVO_CORRIENTE: usar bloque si existe, sino calcular desde naturaleza
        if 'ACTIVO_CORRIENTE' not in valores_por_tag:
            activo_corriente = Decimal('0')
            for detalle in detalles:
                if (detalle.cuenta.grupo.naturaleza == 'Activo' and 
                    detalle.cuenta.bg_bloque == 'ACTIVO_CORRIENTE'):
                    activo_corriente += detalle.saldo or Decimal('0')
            valores_por_tag['ACTIVO_CORRIENTE'] = activo_corriente
        
        # PASIVO_CORRIENTE: siempre calcular desde bg_bloque
        # Usar el valor de valores_por_bloque si existe, sino calcular directamente
        if 'PASIVO_CORRIENTE' in valores_por_bloque:
            valores_por_tag['PASIVO_CORRIENTE'] = valores_por_bloque['PASIVO_CORRIENTE']
        else:
            pasivo_corriente = Decimal('0')
            for detalle in detalles:
                if (detalle.cuenta.grupo.naturaleza == 'Pasivo' and 
                    detalle.cuenta.bg_bloque == 'PASIVO_CORRIENTE'):
                    pasivo_corriente += detalle.saldo or Decimal('0')
            valores_por_tag['PASIVO_CORRIENTE'] = pasivo_corriente
        
        # PATRIMONIO_TOTAL: siempre calcular desde naturaleza
        # Usar el valor de valores_por_bloque si existe, sino calcular directamente
        if 'PATRIMONIO' in valores_por_bloque:
            valores_por_tag['PATRIMONIO_TOTAL'] = valores_por_bloque['PATRIMONIO']
        else:
            patrimonio = Decimal('0')
            for detalle in detalles:
                if detalle.cuenta.grupo.naturaleza == 'Patrimonio':
                    patrimonio += detalle.saldo or Decimal('0')
            valores_por_tag['PATRIMONIO_TOTAL'] = patrimonio
        
        # Asegurar que siempre existan estos valores (inicializar en 0 si no hay datos)
        if 'PASIVO_CORRIENTE' not in valores_por_tag:
            valores_por_tag['PASIVO_CORRIENTE'] = Decimal('0')
        if 'PATRIMONIO_TOTAL' not in valores_por_tag:
            valores_por_tag['PATRIMONIO_TOTAL'] = Decimal('0')
        if 'ACTIVO_CORRIENTE' not in valores_por_tag:
            valores_por_tag['ACTIVO_CORRIENTE'] = Decimal('0')
    
    return valores_por_tag

@transaction.atomic
def calcular_y_guardar_ratios(empresa, periodo, tipo_estado='RES'):
    """
    Calcula y guarda todos los ratios financieros para una empresa y período.
    
    NUEVO FLUJO (directo desde ratio_tag):
    1. BalanceDetalle: Saldos de cuentas del balance
    2. Cuenta.ratio_tag: Agrupa cuentas por ratio_tag
    3. calcular_valores_desde_ratio_tag(): Suma saldos por ratio_tag
    4. RatioDef: Fórmulas que usan claves de ratio_tag (ej: (ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE))
    5. ResultadoRatio: Almacenamiento del resultado calculado
    
    El proceso:
    - Calcula valores directamente desde las cuentas usando ratio_tag
    - Obtiene valores de ambos tipos de estado (BAL y RES) si es necesario
    - Para cada RatioDef, reemplaza las claves en la fórmula con los valores reales
    - Evalúa la expresión matemática
    - Si el ratio es porcentaje, multiplica por 100
    - Guarda el resultado en ResultadoRatio
    
    Args:
        empresa: Instancia de Empresa
        periodo: Instancia de Periodo
        tipo_estado: 'BAL' o 'RES' (por defecto 'RES')
        
    Returns:
        list: Lista de diccionarios con {'clave': str, 'nombre': str, 'valor': Decimal}
    """
    # Calcular valores directamente desde ratio_tag para el tipo de estado especificado
    valores_ratio_tag = calcular_valores_desde_ratio_tag(empresa, periodo, tipo_estado)
    
    # También obtener valores del otro tipo de estado si existe (para ratios que combinan ambos)
    tipo_otro = 'RES' if tipo_estado == 'BAL' else 'BAL'
    try:
        valores_otro = calcular_valores_desde_ratio_tag(empresa, periodo, tipo_otro)
        valores_ratio_tag.update(valores_otro)
    except:
        pass
    
    # También intentar obtener valores desde estado_dict (para compatibilidad)
    # pero usar los valores de ratio_tag como prioridad
    try:
        data_estado = estado_dict(empresa, periodo, tipo_estado)
        cache_estado = {k: v['monto'] for k, v in data_estado.items()}
    except:
        cache_estado = {}
    
    # Intentar también el otro tipo de estado
    try:
        data_otro = estado_dict(empresa, periodo, tipo_otro)
        cache_otro = {k: v['monto'] for k, v in data_otro.items()}
        cache_estado.update(cache_otro)
    except:
        pass
    
    # Combinar: priorizar valores_ratio_tag, luego cache_estado
    cache = {**cache_estado, **valores_ratio_tag}
    
    # Debug: Log de valores calculados (solo en desarrollo)
    # logger.debug(f"Valores calculados para {empresa.nit} período {periodo}: {cache}")
    
    # Asegurar que los ratios base existan (crear si no existen)
    ratios_base = [
        ('LIQUIDEZ_CORRIENTE', 'Liquidez Corriente', '(ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)', False),
        ('ENDEUDAMIENTO', 'Endeudamiento', '(PASIVO_CORRIENTE)/(TOTAL_ACTIVO)', True),
        ('MARGEN_NETO', 'Margen Neto', '(UTILIDAD_NETA)/(VENTAS_NETAS)', True),
        ('ROA', 'Rentabilidad sobre Activos (ROA)', '(UTILIDAD_NETA)/(TOTAL_ACTIVO)', True),
        ('ROE', 'Rentabilidad sobre Patrimonio (ROE)', '(UTILIDAD_NETA)/(PATRIMONIO_TOTAL)', True),
        ('ROTACION_ACTIVOS', 'Rotación de Activos', '(VENTAS_NETAS)/(TOTAL_ACTIVO)', False),
        ('APALANCAMIENTO', 'Apalancamiento', '(TOTAL_ACTIVO)/(PATRIMONIO_TOTAL)', False),
        ('CAPITAL_TRABAJO', 'Capital de Trabajo', '(ACTIVO_CORRIENTE)-(PASIVO_CORRIENTE)', False),
        ('RAZON_ACTIVOS_CORRIENTES', 'Razón de Activos Corrientes', '(ACTIVO_CORRIENTE)/(TOTAL_ACTIVO)', True),
        ('RAZON_PATRIMONIO', 'Razón de Patrimonio', '(PATRIMONIO_TOTAL)/(TOTAL_ACTIVO)', True),
    ]
    for clave, nombre, formula, porcentaje in ratios_base:
        RatioDef.objects.get_or_create(
            clave=clave,
            defaults={'nombre': nombre, 'formula': formula, 'porcentaje': porcentaje}
        )
    
    resultados = []
    for r in RatioDef.objects.all():
        expr = r.formula
        # Reemplazar claves en la fórmula con valores del cache
        for k, m in cache.items():
            expr = expr.replace(k, f'({m})')
        # Reemplazar claves faltantes con 0
        expr = _replace_missing(expr)

        try:
            # Verificar división por cero antes de evaluar
            # Buscar patrones de división como (X)/(Y) donde Y podría ser 0
            division_pattern = r'\(([^)]+)\)\s*/\s*\(([^)]+)\)'
            matches = re.findall(division_pattern, expr)
            division_por_cero = False
            for num, den in matches:
                try:
                    den_val = Decimal(den)
                    if den_val == 0:
                        division_por_cero = True
                        break
                except:
                    pass
            
            if division_por_cero:
                val = None
            else:
                # No hay división por cero, evaluar normalmente
                val = _eval(ast.parse(expr, mode='eval').body)
                if r.porcentaje:
                    val *= Decimal('100')
        except (ZeroDivisionError, ValueError, TypeError) as e:
            val = None
        except Exception as e:
            # Para otros errores, intentar evaluar de todas formas
            try:
                val = _eval(ast.parse(expr, mode='eval').body)
                if r.porcentaje:
                    val *= Decimal('100')
            except:
                val = None
        ResultadoRatio.objects.update_or_create(
            empresa=empresa,
            periodo=periodo,
            ratio=r,
            defaults={'valor': val}
        )
        resultados.append({'clave': r.clave, 'nombre': r.nombre, 'valor': val})

    return resultados

# Alias por compatibilidad (si en algún lado lo llamaste así):

