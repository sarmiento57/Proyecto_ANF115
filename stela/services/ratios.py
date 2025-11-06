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
