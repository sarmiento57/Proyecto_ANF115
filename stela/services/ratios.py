import ast, operator, re
from decimal import Decimal
from django.db import transaction
from stela.models.finanzas import RatioDef, ResultadoRatio
from .estados import estado_dict

OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
       ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.USub: operator.neg}

def _eval(node):
    if isinstance(node, ast.Num): return Decimal(str(node.n))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -_eval(node.operand)
    if isinstance(node, ast.BinOp): return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("Expresión no soportada")

def _replace_missing(expr):
    return re.sub(r'\b[A-Z_][A-Z0-9_]*\b', '(0)', expr)

@transaction.atomic
def calcular_y_guardar_ratios(empresa, periodo, tipo_estado='RES'):
    """
    Calcula y guarda todos los ratios financieros para una empresa y período.
    
    Flujo completo de cálculo de ratios:
    1. BalanceDetalle: Saldos de cuentas del balance
    2. MapeoCuentaLinea: Mapeo de cuentas a líneas de estado
    3. LineaEstado: Agregación de valores por línea (ej: ACTIVO_CORRIENTE)
    4. RatioDef: Fórmulas que usan claves de LineaEstado (ej: (ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE))
    5. ResultadoRatio: Almacenamiento del resultado calculado
    
    El proceso:
    - Obtiene los valores de líneas de estado usando estado_dict()
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
    data = estado_dict(empresa, periodo, tipo_estado)
    cache = {k: v['monto'] for k,v in data.items()}
    resultados = []
    for r in RatioDef.objects.all():
        expr = r.formula
        for k,m in cache.items():
            expr = expr.replace(k, f'({m})')
        expr = _replace_missing(expr)
        try:
            val = _eval(ast.parse(expr, mode='eval').body)
            if r.porcentaje:
                val *= Decimal('100')
        except Exception:
            val = None
        ResultadoRatio.objects.update_or_create(
            empresa=empresa, periodo=periodo, ratio=r, defaults={'valor': val}
        )
        resultados.append({'clave': r.clave, 'nombre': r.nombre, 'valor': val})
    return resultados
