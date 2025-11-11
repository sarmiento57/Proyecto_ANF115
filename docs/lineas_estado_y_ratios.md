# Líneas de Estado y Cálculo de Ratios

## Índice
1. [Introducción](#introducción)
2. [Líneas de Estado Disponibles](#líneas-de-estado-disponibles)
3. [Mapeo Automático](#mapeo-automático)
4. [Ratios y Fórmulas](#ratios-y-fórmulas)
5. [Agregar Nuevas Líneas de Estado](#agregar-nuevas-líneas-de-estado)
6. [Agregar Nuevos Ratios](#agregar-nuevos-ratios)
7. [Mapeo Manual (Ajustes Finos)](#mapeo-manual-ajustes-finos)
8. [Flujo de Cálculo](#flujo-de-cálculo)

---

## Introducción

Las **líneas de estado** son agregaciones de valores contables que se usan para calcular ratios financieros. Representan conceptos como "Total Activo", "Activo Corriente", "Ventas Netas", etc.

### Relación con Bloques del Catálogo

Las líneas de estado se relacionan directamente con los bloques definidos en el catálogo de cuentas:

- **Bloques del Balance General (bg_bloque)**: Se mapean a líneas de estado de tipo `BAL`
- **Bloques del Estado de Resultados (er_bloque)**: Se mapean a líneas de estado de tipo `RES`

### Uso en Ratios

Los ratios financieros se calculan usando fórmulas que referencian las claves de las líneas de estado. Por ejemplo:

- `LIQUIDEZ_CORRIENTE = (ACTIVO_CORRIENTE) / (PASIVO_CORRIENTE)`
- `MARGEN_NETO = (UTILIDAD_NETA) / (VENTAS_NETAS)`

---

## Líneas de Estado Disponibles

### Balance General (BAL)

| Clave | Nombre | Base Vertical | Descripción |
|-------|--------|---------------|-------------|
| `TOTAL_ACTIVO` | Total Activo | Sí | Suma de todos los activos (corriente + no corriente). Base para análisis vertical del Balance. |
| `ACTIVO_CORRIENTE` | Activo Corriente | No | Suma de todas las cuentas con `bg_bloque='ACTIVO_CORRIENTE'` |
| `PASIVO_CORRIENTE` | Pasivo Corriente | No | Suma de todas las cuentas con `bg_bloque='PASIVO_CORRIENTE'` |
| `PATRIMONIO_TOTAL` | Patrimonio | No | Suma de todas las cuentas con `bg_bloque='PATRIMONIO'` |

### Estado de Resultados (RES)

| Clave | Nombre | Base Vertical | Descripción |
|-------|--------|---------------|-------------|
| `VENTAS_NETAS` | Ventas Netas | Sí | Suma de todas las cuentas con `er_bloque='VENTAS_NETAS'`. Base para análisis vertical del Estado de Resultados. |
| `COSTO_VENTAS` | Costo de Ventas | No | Suma de todas las cuentas con `er_bloque='COSTO_NETO_VENTAS'` |
| `UTILIDAD_NETA` | Utilidad Neta | No | **Calculada automáticamente** a partir de los bloques del Estado de Resultados. No se mapea directamente desde cuentas. |

**Nota sobre UTILIDAD_NETA**: Esta línea no se mapea directamente desde cuentas. Se calcula en `calcular_totales_por_seccion()` usando la fórmula:

```
UTILIDAD_NETA = Utilidad Operativa - Gasto Financiero + Otros Ingresos - Otros Gastos
```

Donde:
- `Utilidad Operativa = Utilidad Bruta - Gastos Operativos`
- `Utilidad Bruta = Ventas Netas - Costo Neto de Ventas`

---

## Mapeo Automático

El sistema mapea automáticamente las cuentas del catálogo a líneas de estado basándose en los bloques definidos en la plantilla.

### Reglas de Mapeo

1. **ACTIVO_CORRIENTE**:
   - Todas las cuentas con `bg_bloque='ACTIVO_CORRIENTE'` → `LineaEstado.clave='ACTIVO_CORRIENTE'`

2. **PASIVO_CORRIENTE**:
   - Todas las cuentas con `bg_bloque='PASIVO_CORRIENTE'` → `LineaEstado.clave='PASIVO_CORRIENTE'`

3. **VENTAS_NETAS**:
   - Todas las cuentas con `er_bloque='VENTAS_NETAS'` → `LineaEstado.clave='VENTAS_NETAS'`

4. **TOTAL_ACTIVO**:
   - Todas las cuentas con `grupo.naturaleza='Activo'` y `bg_bloque` en `['ACTIVO_CORRIENTE', 'ACTIVO_NO_CORRIENTE']` → `LineaEstado.clave='TOTAL_ACTIVO'`

### Cuándo se Ejecuta

El mapeo automático se ejecuta:

1. **Al cargar un catálogo** (Paso 2 del asistente de carga)
   - Se ejecuta automáticamente después de crear/actualizar las cuentas
   - Muestra un mensaje indicando cuántas cuentas fueron mapeadas

2. **Manual desde el formulario de mapeo**
   - Botón "Re-mapear Automáticamente" en `/stela/catalogo/mapeo/<catalogo_id>/`
   - Útil para actualizar mapeos después de modificar bloques en el catálogo

### Implementación

El mapeo automático está implementado en `stela/services/mapeo_automatico.py`:

```python
from stela.services.mapeo_automatico import mapear_cuentas_por_bloques

# Mapear cuentas de un catálogo
resumen = mapear_cuentas_por_bloques(catalogo)
# Retorna: {'ACTIVO_CORRIENTE': 15, 'PASIVO_CORRIENTE': 8, ...}
```

---

## Ratios y Fórmulas

### Ratios Disponibles

| Clave | Nombre | Fórmula | Porcentaje | Descripción |
|-------|--------|---------|------------|-------------|
| `LIQUIDEZ_CORRIENTE` | Liquidez Corriente | `(ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)` | No | Mide la capacidad de la empresa para pagar sus obligaciones a corto plazo |
| `ENDEUDAMIENTO` | Endeudamiento | `(PASIVO_CORRIENTE)/(TOTAL_ACTIVO)` | Sí | Porcentaje de activos financiados con pasivo corriente |
| `MARGEN_NETO` | Margen Neto | `(UTILIDAD_NETA)/(VENTAS_NETAS)` | Sí | Porcentaje de utilidad neta sobre ventas |

### Cómo se Calculan

El cálculo de ratios sigue este proceso:

1. **Obtener valores de líneas de estado** (`estado_dict()`):
   - Lee los saldos de `BalanceDetalle`
   - Suma los saldos de las cuentas mapeadas a cada `LineaEstado`
   - Retorna un diccionario: `{'ACTIVO_CORRIENTE': 150000, 'PASIVO_CORRIENTE': 75000, ...}`

2. **Evaluar fórmulas** (`calcular_y_guardar_ratios()`):
   - Para cada `RatioDef`, reemplaza las claves en la fórmula con los valores reales
   - Ejemplo: `(ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)` → `(150000)/(75000)` → `2.0`
   - Si `porcentaje=True`, multiplica por 100

3. **Guardar resultados**:
   - Almacena en `ResultadoRatio` (empresa, período, ratio, valor)

### Almacenamiento

Los resultados se guardan en el modelo `ResultadoRatio`:

```python
ResultadoRatio.objects.filter(
    empresa=empresa,
    periodo=periodo,
    ratio=ratio_def
).first()
```

---

## Agregar Nuevas Líneas de Estado

Para agregar una nueva línea de estado:

### Paso 1: Agregar a seed_finanzas.py

Edita `stela/management/commands/seed_finanzas.py`:

```python
LINEAS = [
  ('BAL','TOTAL_ACTIVO','Total Activo', True),
  ('BAL','ACTIVO_CORRIENTE','Activo Corriente', False),
  # Agregar nueva línea
  ('BAL','ACTIVO_NO_CORRIENTE','Activo No Corriente', False),
  # ...
]
```

Formato: `(estado, clave, nombre, base_vertical)`

### Paso 2: Ejecutar comando seed

```bash
python manage.py seed_finanzas
```

### Paso 3: Actualizar mapeo automático (si aplica)

Si la nueva línea debe mapearse automáticamente desde bloques, edita `stela/services/mapeo_automatico.py`:

```python
mapeo_bloques = {
    'ACTIVO_NO_CORRIENTE': 'ACTIVO_NO_CORRIENTE',  # Nueva regla
    # ...
}
```

### Paso 4: Crear/actualizar ratios que la usen

Agrega ratios que usen la nueva línea (ver sección siguiente).

---

## Agregar Nuevos Ratios

Para agregar un nuevo ratio financiero:

### Paso 1: Agregar a seed_finanzas.py

Edita `stela/management/commands/seed_finanzas.py`:

```python
RATIOS = [
  ('LIQUIDEZ_CORRIENTE','Liquidez Corriente','(ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)', False),
  # Agregar nuevo ratio
  ('ROA','Rentabilidad del Activo','(UTILIDAD_NETA)/(TOTAL_ACTIVO)', True),
  # ...
]
```

Formato: `(clave, nombre, formula, porcentaje)`

**Importante**: La fórmula debe usar claves de `LineaEstado` (no nombres de cuentas).

### Paso 2: Ejecutar comando seed

```bash
python manage.py seed_finanzas
```

### Paso 3: El ratio se calculará automáticamente

El ratio se calculará automáticamente cuando se llame a `calcular_y_guardar_ratios()`:

```python
from stela.services.ratios import calcular_y_guardar_ratios

resultados = calcular_y_guardar_ratios(empresa, periodo, tipo_estado='RES')
# El nuevo ratio estará incluido en los resultados
```

### Ejemplo de Fórmulas Válidas

- `(ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)` - División
- `(UTILIDAD_NETA)/(VENTAS_NETAS)` - División
- `(ACTIVO_CORRIENTE)-(PASIVO_CORRIENTE)` - Resta
- `(VENTAS_NETAS)+(OTROS_INGRESOS)` - Suma

**Nota**: Las claves en las fórmulas deben coincidir exactamente con las claves de `LineaEstado`.

---

## Mapeo Manual (Ajustes Finos)

Aunque el mapeo automático cubre la mayoría de casos, puedes ajustar manualmente el mapeo de cuentas a líneas de estado.

### Cuándo Usar Mapeo Manual

- Casos especiales donde el mapeo automático no es suficiente
- Necesitas excluir ciertas cuentas de una línea
- Necesitas mapear una cuenta a múltiples líneas (requiere múltiples registros de `MapeoCuentaLinea`)

### Cómo Acceder

1. Navega a la vista de mapeo: `/stela/catalogo/mapeo/<catalogo_id>/`
2. Selecciona las cuentas para cada línea de estado
3. Guarda el mapeo

### Mapeo Manual vs Automático

- **Automático**: Basado en bloques (`bg_bloque`, `er_bloque`). Se ejecuta al cargar catálogo.
- **Manual**: Selección explícita de cuentas. Sobrescribe el mapeo automático para las líneas modificadas.

**Recomendación**: Usa mapeo automático como base y ajusta manualmente solo cuando sea necesario.

---

## Flujo de Cálculo

El flujo completo de cálculo de ratios es:

```
1. BalanceDetalle (saldos de cuentas)
   ↓
2. MapeoCuentaLinea (mapeo cuenta → línea)
   ↓
3. LineaEstado (agregación por línea)
   ↓
4. estado_dict() (valores calculados)
   ↓
5. RatioDef (fórmulas)
   ↓
6. calcular_y_guardar_ratios() (evaluación)
   ↓
7. ResultadoRatio (resultados almacenados)
```

### Ejemplo Práctico

1. **BalanceDetalle**: Cuenta 1101 (Caja) tiene saldo = 50,000
2. **MapeoCuentaLinea**: Cuenta 1101 está mapeada a `ACTIVO_CORRIENTE` con signo = 1
3. **LineaEstado**: `ACTIVO_CORRIENTE` suma todas las cuentas mapeadas = 150,000
4. **estado_dict()**: Retorna `{'ACTIVO_CORRIENTE': {'monto': 150000, ...}}`
5. **RatioDef**: `LIQUIDEZ_CORRIENTE = (ACTIVO_CORRIENTE)/(PASIVO_CORRIENTE)`
6. **calcular_y_guardar_ratios()**: Reemplaza → `(150000)/(75000)` → Evalúa → `2.0`
7. **ResultadoRatio**: Guarda `valor=2.0` para empresa, período y ratio

### Archivos Clave

- `stela/services/estados.py`: `estado_dict()` - Calcula valores de líneas
- `stela/services/ratios.py`: `calcular_y_guardar_ratios()` - Calcula ratios
- `stela/services/mapeo_automatico.py`: `mapear_cuentas_por_bloques()` - Mapeo automático
- `stela/models/finanzas.py`: Modelos `LineaEstado`, `MapeoCuentaLinea`, `RatioDef`, `ResultadoRatio`

---

## Resumen

- **Líneas de estado**: Agregaciones de valores contables (ej: ACTIVO_CORRIENTE, VENTAS_NETAS)
- **Mapeo automático**: Se ejecuta al cargar catálogo, basado en bloques (`bg_bloque`, `er_bloque`)
- **Ratios**: Fórmulas que usan claves de líneas de estado
- **Flujo**: BalanceDetalle → MapeoCuentaLinea → LineaEstado → RatioDef → ResultadoRatio
- **Agregar líneas/ratios**: Editar `seed_finanzas.py` y ejecutar `python manage.py seed_finanzas`

