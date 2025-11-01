import ast, operator, re
from decimal import Decimal
from django.db import transaction
from stela.models.finanzas import RatioDef, ResultadoRatio
from .estados import estado_dict

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

@transaction.atomic
def calcular_ratios(empresa, periodo, tipo_estado='RES'):
    """
    Calcula (y persiste) los RatioDef para empresa/periodo.
    Devuelve [{'clave','nombre','valor'}, ...]
    """
    # Cargamos los montos (dicc: clave -> {'monto','nombre','base'})
    data = estado_dict(empresa, periodo, tipo_estado)
    cache = {k: v['monto'] for k, v in data.items()}

    resultados = []
    for r in RatioDef.objects.all():   # <- OJO: objects (con "s")
        expr = (r.formula or "")
        # Sustituimos cada CLAVE por su monto
        for k, m in cache.items():
            expr = expr.replace(k, f'({m})')
        # Cualquier identificador no sustituido => 0
        expr = _replace_missing(expr)

        try:
            val = _eval(ast.parse(expr, mode='eval').body)
            if getattr(r, "porcentaje", False):
                val *= Decimal('100')
        except Exception:
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
calcular_y_guardar_ratios = calcular_ratios
