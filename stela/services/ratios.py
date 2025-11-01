# stela/services/ratios.py
import ast, operator
from decimal import Decimal
from stela.models.estados import RatioDef
from stela.services.estados import estado_dict

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg}

def _eval(node):
    if isinstance(node, ast.Num): return Decimal(str(node.n))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -_eval(node.operand)
    if isinstance(node, ast.BinOp): return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("Expresión no soportada")

def calcular_ratios(empresa, estado, anio, mes=None):
    # usamos el diccionario del estado para resolver claves
    data = estado_dict(empresa, estado, anio, mes)
    cache = {k: v["monto"] for k, v in data.items()}

    resultados = []
    for r in RatioDef.objects.all():
        expr = r.formula
        # reemplazo simple por claves; si clave no existe, asúmela 0
        for k, monto in cache.items():
            expr = expr.replace(k, f"({monto})")
        # claves que no estén presentes -> 0
        expr = re_claves_a_cero(expr)
        try:
            val = _eval(ast.parse(expr, mode='eval').body)
            if r.porcentaje: val *= Decimal('100')
        except Exception:
            val = None
        resultados.append({"clave": r.clave, "nombre": r.nombre, "valor": val})
    return resultados

def re_claves_a_cero(expr):
    # reemplaza tokens MAYUSCULAS_CON_GUION que no sean números ni operadores por 0
    import re
    def repl(m): return "(0)"
    return re.sub(r'\b[A-Z_][A-Z0-9_]*\b', repl, expr)

def benchmarking_por_ciiu(ciiu_codigo, ratios_empresas):
    """
    ratios_empresas: lista de dicts {"empresa": Empresa, "ratios": {clave: Decimal|None}}
    Agrupa por CIIU (ya lo tienes en Empresa.idCiiu) y devuelve promedio y desviación.
    """
    from statistics import mean, pstdev
    # construir por clave
    pool = {}
    for item in ratios_empresas:
        for k, v in item["ratios"].items():
            if v is None: continue
            pool.setdefault(k, []).append(Decimal(v))
    out = {}
    for k, arr in pool.items():
        if not arr: continue
        prom = mean(arr)
        desv = pstdev(arr) if len(arr) > 1 else Decimal('0')
        out[k] = {"promedio": Decimal(prom), "desv": Decimal(desv)}
    return out
