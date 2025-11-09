# Módulo de Catálogo y Carga de Datos

## Índice
1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Modelos de Datos](#modelos-de-datos)
4. [Proceso de Carga de Datos](#proceso-de-carga-de-datos)
5. [Uso de Excel](#uso-de-excel)
6. [Plantillas Excel](#plantillas-excel)
7. [Flujo de Trabajo](#flujo-de-trabajo)
8. [Características Especiales](#características-especiales)
9. [Validaciones y Seguridad](#validaciones-y-seguridad)

---

## Introducción

El módulo de catálogo es el sistema central para gestionar las cuentas contables de las empresas y cargar sus estados financieros. Este módulo permite:

- **Gestionar catálogos únicos por empresa**: Cada empresa tiene un solo catálogo que no cambia por año
- **Cargar estados financieros**: Balance General y Estado de Resultados por período
- **Automatizar cálculos**: Subtotales, totales y ratios financieros
- **Usar Excel como formato principal**: Plantillas inteligentes con fórmulas y protección de celdas

---

## Arquitectura del Sistema

### Componentes Principales

```
stela/
├── models/
│   └── catalogo.py          # Modelos: Catalogo, GrupoCuenta, Cuenta
├── services/
│   ├── plantillas.py        # Generación de plantillas Excel
│   └── estados.py           # Cálculo de estados financieros
├── views.py                 # Vistas de carga y gestión
├── templates/
│   ├── dashboard/
│   │   ├── dashboard.html           # Dashboard principal
│   │   └── empresa_detalles.html    # Vista de detalles de empresa
│   └── stela/catalogo/
│       └── upload.html              # Asistente de carga (3 pasos)
└── urls.py                  # Rutas del módulo
```

### Flujo de Datos

```
Usuario → Dashboard → Detalles de Empresa → Asistente de Carga
                                              ↓
                                    [Paso 1: Seleccionar Empresa]
                                              ↓
                                    [Paso 2: Cargar Catálogo]
                                              ↓
                                    [Paso 3: Cargar Estados Financieros]
                                              ↓
                                    Base de Datos
```

---

## Modelos de Datos

### 1. Catalogo

**Relación**: `OneToOneField` con `Empresa` (una empresa = un catálogo)

```python
class Catalogo(models.Model):
    id_catalogo = models.AutoField(primary_key=True)
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
```

**Características**:
- **Único por empresa**: No hay catálogos por año, solo uno por empresa
- **Inmutable una vez creado**: El catálogo base no cambia, solo se pueden agregar cuentas
- **Historial**: Se registra fecha de creación y última actualización

### 2. GrupoCuenta

**Relación**: `ForeignKey` con `Catalogo` (un catálogo tiene múltiples grupos)

```python
class GrupoCuenta(models.Model):
    NAT_CHOICES = [
        ('Activo', 'Activo'),
        ('Pasivo', 'Pasivo'),
        ('Patrimonio', 'Patrimonio'),
        ('Ingreso', 'Ingreso'),
        ('Gasto', 'Gasto')
    ]
    catalogo = models.ForeignKey(Catalogo, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    naturaleza = models.CharField(max_length=20, choices=NAT_CHOICES)
```

**Características**:
- **Naturaleza como string completo**: "Activo", "Pasivo", etc. (no caracteres únicos)
- **Agrupa cuentas**: Las cuentas se organizan por grupos (ej: "Activo Corriente", "Pasivo Corriente")

### 3. Cuenta

**Relación**: `ForeignKey` con `GrupoCuenta` (un grupo tiene múltiples cuentas)

```python
class Cuenta(models.Model):
    grupo = models.ForeignKey(GrupoCuenta, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=30)  # 1101, 41-01, etc.
    nombre = models.CharField(max_length=180)
    aparece_en_balance = models.BooleanField(default=True)
    
    # Bloques del Balance General
    bg_bloque = models.CharField(
        max_length=50,
        choices=BG_BLOQUES,
        help_text='Bloque del Balance General donde se mostrará'
    )
    
    # Bloques del Estado de Resultados
    er_bloque = models.CharField(
        max_length=50,
        choices=ER_BLOQUES,
        help_text='Bloque del Estado de Resultados al que pertenece'
    )
    
    # Tags para ratios
    ratio_tag = models.CharField(
        max_length=50,
        choices=RATIO_TAGS,
        help_text='Tag constante para cálculo de ratios. Múltiples cuentas pueden tener el mismo tag.'
    )
```

**Campos Especiales**:

#### `bg_bloque` (Balance General)
- `ACTIVO_CORRIENTE`: Activos corrientes
- `ACTIVO_NO_CORRIENTE`: Activos no corrientes
- `PASIVO_CORRIENTE`: Pasivos corrientes
- `PASIVO_NO_CORRIENTE`: Pasivos no corrientes
- `PATRIMONIO`: Patrimonio

#### `er_bloque` (Estado de Resultados)
- `VENTAS_NETAS`: Ventas netas
- `COSTO_NETO_VENTAS`: Costo neto de ventas
- `GASTOS_OPERATIVOS`: Gastos operativos
- `OTROS_INGRESOS`: Otros ingresos
- `OTROS_GASTOS`: Otros gastos
- `GASTO_FINANCIERO`: Gasto financiero
- `IMPUESTO_SOBRE_LA_RENTA`: Impuesto sobre la renta

#### `ratio_tag` (Tags para Ratios)
- **Propósito**: Agrupar cuentas para cálculo automático de ratios
- **Comportamiento**: Si múltiples cuentas tienen el mismo `ratio_tag`, sus saldos se suman automáticamente
- **Ejemplos**:
  - `EFECTIVO`: Suma de Caja + Bancos + Equivalentes de Efectivo
  - `VENTAS_NETAS`: Suma de Ventas - Descuentos - Devoluciones
  - `ACTIVO_CORRIENTE`: Suma de todos los activos corrientes

---

## Proceso de Carga de Datos

El sistema utiliza un **asistente de 3 pasos** para cargar datos:

### Paso 1: Selección de Empresa

**Objetivo**: Seleccionar la empresa para la cual se cargarán los datos

**Características**:
- Lista desplegable con todas las empresas del usuario
- Si se accede desde la vista de detalles de empresa, la empresa ya está preseleccionada
- Si la empresa ya tiene catálogo, automáticamente salta al Paso 3

**Vista**: `stela/templates/stela/catalogo/upload.html` (Paso 1)

### Paso 2: Carga de Catálogo

**Objetivo**: Cargar el catálogo de cuentas contables de la empresa

**Formato**: Excel con hoja "Catálogo"

**Columnas Requeridas**:
1. `Código`: Código de la cuenta (ej: "1101", "41-01")
2. `Nombre`: Nombre de la cuenta (ej: "Caja", "Ventas")
3. `Grupo`: Nombre del grupo (ej: "Activo Corriente", "Ingresos")
4. `Naturaleza`: Naturaleza de la cuenta (Activo, Pasivo, Patrimonio, Ingreso, Gasto)
5. `BG Bloque`: Bloque del Balance General (opcional)
6. `ER Bloque`: Bloque del Estado de Resultados (opcional)
7. `Ratio Tag`: Tag para cálculo de ratios (opcional)

**Proceso**:
1. El sistema lee el archivo Excel
2. Para cada fila:
   - Crea o actualiza el `GrupoCuenta`
   - Crea o actualiza la `Cuenta`
   - Asigna `bg_bloque`, `er_bloque` y `ratio_tag` si están presentes
3. Si el catálogo ya existe, se actualizan las cuentas existentes y se agregan nuevas

**Validaciones**:
- El archivo debe ser Excel (.xlsx o .xls)
- Debe tener una hoja llamada "Catálogo"
- Las columnas requeridas deben estar presentes
- La naturaleza debe ser una de las opciones válidas

**Vista**: `stela/templates/stela/catalogo/upload.html` (Paso 2)

### Paso 3: Carga de Estados Financieros

**Objetivo**: Cargar los valores de debe/haber para Balance General y Estado de Resultados

**Formato**: Excel con dos hojas:
- `BalanceGeneral`: Balance General
- `EstadoResultados`: Estado de Resultados

**Estructura de las Hojas**:

#### BalanceGeneral
- `Código`: Código de la cuenta
- `Cuenta`: Nombre de la cuenta
- `Debe`: Valor del debe (verde claro)
- `Haber`: Valor del haber (azul claro)
- `Total`: Fórmula automática (Haber - Debe)

#### EstadoResultados
- `Código`: Código de la cuenta
- `Cuenta`: Nombre de la cuenta
- `Debe`: Valor del debe (verde claro)
- `Haber`: Valor del haber (azul claro)
- `Total`: Fórmula automática (Haber - Debe)

**Proceso**:
1. El usuario ingresa el año del período
2. El sistema lee ambas hojas del Excel
3. Para cada cuenta:
   - Busca la cuenta en el catálogo por código
   - Si existe, crea o actualiza el `BalanceDetalle`
   - Si no existe, se ignora (no falla el proceso)
4. Crea o actualiza el `Periodo` y los `Balance` (BAL y RES)
5. Recalcula los saldos según la naturaleza del grupo

**Validaciones**:
- El archivo debe ser Excel (.xlsx o .xls)
- Debe tener las hojas "BalanceGeneral" y "EstadoResultados"
- El año debe ser un número válido
- Los valores numéricos se validan al convertir a Decimal

**Vista**: `stela/templates/stela/catalogo/upload.html` (Paso 3)

---

## Uso de Excel

### Formato Principal

**Excel es el único formato soportado** para carga de datos. CSV está deprecado.

### Librería Utilizada

**openpyxl**: Librería Python para leer y escribir archivos Excel (.xlsx)

```python
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Protection, Border, Side
```

### Lectura de Archivos

```python
# Cargar archivo Excel
wb = load_workbook(archivo, data_only=True)

# Leer hoja específica
ws = wb['Catálogo']  # o 'BalanceGeneral', 'EstadoResultados'

# Iterar filas (empezando desde fila 2 para saltar encabezados)
for row in ws.iter_rows(min_row=2, values_only=True):
    codigo = row[0]
    nombre = row[1]
    # ...
```

### Escritura de Archivos

```python
# Crear nuevo workbook
wb = Workbook()

# Crear hoja
ws = wb.create_sheet("Catálogo")

# Escribir datos
ws.append(['Código', 'Nombre', 'Grupo', ...])

# Aplicar estilos
from openpyxl.styles import Font, PatternFill
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
ws['A1'].font = header_font
ws['A1'].fill = header_fill
```

---

## Plantillas Excel

### Plantilla de Catálogo

**Ubicación**: Generada por `stela/services/plantillas.py::generar_plantilla_catalogo_excel()`

**Características**:
- **Hoja "Catálogo"**: Lista de cuentas base con todas las columnas
- **Hoja "Leyenda"**: Explicación de campos y uso
- **Protección de celdas**: Solo se pueden editar `BG Bloque`, `ER Bloque` y `Ratio Tag`
- **Cuentas base**: Incluye 36+ cuentas predefinidas necesarias para ratios

**Estructura**:

| Código | Nombre | Grupo | Naturaleza | BG Bloque | ER Bloque | Ratio Tag |
|--------|--------|-------|------------|-----------|-----------|-----------|
| 1101 | Caja | Activo Corriente | Activo | ACTIVO_CORRIENTE | | EFECTIVO |
| 1102 | Bancos | Activo Corriente | Activo | ACTIVO_CORRIENTE | | EFECTIVO |
| ... | ... | ... | ... | ... | ... | ... |

**Protección**:
- **Bloqueadas**: Código, Nombre, Grupo, Naturaleza
- **Editables**: BG Bloque, ER Bloque, Ratio Tag

### Plantilla de Estados Financieros

**Ubicación**: Generada por `stela/services/plantillas.py::generar_plantilla_estados_excel()`

**Características**:
- **Dos hojas**: "BalanceGeneral" y "EstadoResultados"
- **Fórmulas automáticas**: Total = Haber - Debe
- **Subtotales automáticos**: Fórmulas SUM para cada bloque
- **Protección de celdas**: Solo se pueden editar Debe y Haber
- **Guía visual**: Colores verde (Debe) y azul (Haber)
- **Indentación**: En Estado de Resultados, las cuentas están indentadas bajo sus bloques
- **Bordes**: Subtotales tienen borde superior

**Estructura BalanceGeneral**:

| Código | Cuenta | Debe | Haber | Total |
|--------|--------|------|-------|-------|
| 1101 | Caja | 0.00 | 0.00 | =C2-D2 |
| 1102 | Bancos | 0.00 | 0.00 | =C3-D3 |
| ... | **Total Activo Corriente** | | | =SUM(E2:E10) |

**Estructura EstadoResultados**:

| Código | Cuenta | Debe | Haber | Total |
|--------|--------|------|-------|-------|
| 4101 | Ventas | 0.00 | 0.00 | =C2-D2 |
| 4102 | Descuentos sobre Ventas | 0.00 | 0.00 | =C3-D3 |
| ... | **Ventas Netas** | | | =SUM(E2:E4) |

**Protección**:
- **Bloqueadas**: Código, Cuenta, Total (y fórmulas)
- **Editables**: Debe, Haber

**Colores**:
- **Verde claro** (`#E8F5E9`): Columnas Debe (para Activos y Gastos)
- **Azul claro** (`#E3F2FD`): Columnas Haber (para Pasivos, Patrimonio e Ingresos)

**Fórmulas**:
- **Total por cuenta**: `=Haber - Debe` (o `=D2-C2` según columna)
- **Subtotales por bloque**: `=SUM(E2:E10)` (suma de columna Total del bloque)

---

## Flujo de Trabajo

### 1. Desde el Dashboard

```
Dashboard → [Cargar Datos] → Asistente (Paso 1)
```

**Botón "Cargar Datos"**: Redirige al asistente desde el paso 1

### 2. Desde Detalles de Empresa

```
Dashboard → [Ver Detalles] → Detalles de Empresa → [Cargar Catálogo] → Asistente (Paso 2)
```

**Características**:
- Si la empresa **no tiene catálogo**: Redirige al Paso 2 con empresa preseleccionada
- Si la empresa **tiene catálogo**: Redirige al Paso 3 con empresa y catálogo preseleccionados

### 3. Proceso Completo

```
1. Usuario selecciona empresa (Paso 1)
   ↓
2. Usuario descarga plantilla de catálogo
   ↓
3. Usuario llena plantilla con sus cuentas
   ↓
4. Usuario carga catálogo (Paso 2)
   ↓
5. Sistema genera plantilla de estados financieros basada en el catálogo
   ↓
6. Usuario descarga plantilla de estados financieros
   ↓
7. Usuario llena plantilla con valores (debe/haber)
   ↓
8. Usuario carga estados financieros (Paso 3)
   ↓
9. Sistema valida, procesa y guarda datos
```

---

## Características Especiales

### 1. Catálogo Único por Empresa

**Diseño**: `OneToOneField` entre `Catalogo` y `Empresa`

**Ventajas**:
- **Consistencia**: Un solo catálogo base para toda la empresa
- **Simplicidad**: No hay que gestionar múltiples catálogos por año
- **Historial**: Los estados financieros se vinculan a períodos, no a catálogos

**Comportamiento**:
- Si una empresa ya tiene catálogo, no se puede crear otro
- Se puede actualizar el catálogo existente agregando nuevas cuentas
- El catálogo es "inmutable" en el sentido de que no cambia su estructura base

### 2. Bloques y Subtotales Automáticos

**Balance General**:
- Las cuentas se agrupan por `bg_bloque`
- Los subtotales se calculan automáticamente sumando las cuentas del bloque
- Ejemplo: `Total Activo Corriente = SUM(cuentas con bg_bloque='ACTIVO_CORRIENTE')`

**Estado de Resultados**:
- Las cuentas se agrupan por `er_bloque`
- Los subtotales se calculan automáticamente
- Ejemplo: `Ventas Netas = SUM(cuentas con er_bloque='VENTAS_NETAS')`

### 3. Ratio Tags

**Propósito**: Agrupar cuentas para cálculo automático de ratios financieros

**Comportamiento**:
- Múltiples cuentas pueden tener el mismo `ratio_tag`
- Al calcular ratios, se suman automáticamente todas las cuentas con el mismo tag
- Ejemplo: `EFECTIVO = Caja + Bancos + Equivalentes de Efectivo`

**Ejemplos de Tags**:
- `EFECTIVO`: Para razón de efectivo
- `VENTAS_NETAS`: Para márgenes y rotaciones
- `ACTIVO_CORRIENTE`: Para razón corriente
- `CUENTAS_POR_COBRAR`: Para rotación de cuentas por cobrar

### 4. Validación Flexible

**Filosofía**: "No fallar si falta una cuenta"

**Comportamiento**:
- Si una cuenta del Excel no existe en el catálogo, se ignora (no falla)
- Si falta una cuenta en el estado financiero, el subtotal se muestra en 0
- El sistema es tolerante a cuentas faltantes

**Ventajas**:
- Permite cargar estados financieros parciales
- No requiere tener todas las cuentas del catálogo
- Facilita la migración gradual de datos

### 5. Plantillas Inteligentes

**Generación Dinámica**:
- La plantilla de estados financieros se genera basándose en el catálogo de la empresa
- Solo incluye las cuentas que tienen `bg_bloque` o `er_bloque` asignados
- Se agrupan automáticamente por bloques

**Características Visuales**:
- **Fórmulas automáticas**: Total y subtotales se calculan automáticamente
- **Protección de celdas**: Solo se pueden editar los campos necesarios
- **Guía visual**: Colores indican dónde llenar Debe (verde) y Haber (azul)
- **Indentación**: En Estado de Resultados, las cuentas están indentadas bajo sus bloques
- **Bordes**: Subtotales tienen borde superior para mejor visualización

---

## Validaciones y Seguridad

### Validaciones de Entrada

1. **Archivo Excel**:
   - Debe ser `.xlsx` o `.xls`
   - Debe tener las hojas requeridas ("Catálogo", "BalanceGeneral", "EstadoResultados")

2. **Datos**:
   - Código de cuenta: Requerido, no vacío
   - Nombre de cuenta: Requerido, no vacío
   - Naturaleza: Debe ser una de las opciones válidas
   - Valores numéricos: Se validan al convertir a Decimal

3. **Empresa**:
   - El usuario solo puede cargar datos para sus propias empresas
   - Validación: `empresa.usuario == request.user`

### Seguridad

1. **Autenticación**: Todas las vistas requieren `@login_required`
2. **Autorización**: Solo se pueden ver/editar empresas del usuario actual
3. **Validación de archivos**: Solo se aceptan archivos Excel
4. **Sanitización**: Los valores se convierten a Decimal para evitar inyección

### Manejo de Errores

1. **Errores de formato**: Mensaje claro al usuario
2. **Errores de datos**: Se registran pero no detienen el proceso completo
3. **Errores de validación**: Se muestran mensajes específicos por error

---

## Ejemplos de Uso

### Ejemplo 1: Cargar Catálogo Nuevo

1. Usuario va al Dashboard
2. Hace clic en "Cargar Datos"
3. Selecciona empresa (Paso 1)
4. Descarga plantilla de catálogo
5. Llena la plantilla con sus cuentas
6. Carga el archivo (Paso 2)
7. Sistema crea el catálogo y redirige al Paso 3

### Ejemplo 2: Cargar Estados Financieros

1. Usuario va a Detalles de Empresa
2. Hace clic en "Cargar Estados Financieros"
3. Sistema redirige al Paso 3 con empresa y catálogo preseleccionados
4. Usuario ingresa el año (ej: 2024)
5. Descarga plantilla de estados financieros
6. Llena la plantilla con valores (debe/haber)
7. Carga el archivo
8. Sistema procesa y guarda los datos

### Ejemplo 3: Actualizar Catálogo

1. Usuario va a Detalles de Empresa
2. Hace clic en "Cargar Catálogo" (aunque ya existe)
3. Sistema muestra advertencia: "Esta empresa ya tiene un catálogo cargado"
4. Usuario carga nuevo archivo con cuentas adicionales
5. Sistema actualiza el catálogo agregando nuevas cuentas

---

## Archivos Clave

### Modelos
- `stela/models/catalogo.py`: Modelos `Catalogo`, `GrupoCuenta`, `Cuenta`

### Servicios
- `stela/services/plantillas.py`: Generación de plantillas Excel
- `stela/services/estados.py`: Cálculo de estados financieros y subtotales

### Vistas
- `stela/views.py::catalogo_upload_csv()`: Vista principal del asistente de carga
- `stela/views.py::empresa_detalles()`: Vista de detalles de empresa
- `stela/views.py::descargar_plantilla_catalogo_excel()`: Descarga plantilla de catálogo
- `stela/views.py::descargar_plantilla_estados_excel()`: Descarga plantilla de estados

### Templates
- `stela/templates/dashboard/dashboard.html`: Dashboard principal
- `stela/templates/dashboard/empresa_detalles.html`: Vista de detalles de empresa
- `stela/templates/stela/catalogo/upload.html`: Asistente de carga (3 pasos)

### URLs
- `/stela/catalogo/upload/`: Asistente de carga
- `/stela/dashboard/empresa/<nit>/`: Detalles de empresa
- `/stela/catalogo/plantilla/excel/`: Descarga plantilla de catálogo
- `/stela/catalogo/plantilla/estados/excel/<catalogo_id>/`: Descarga plantilla de estados

---

## Notas Técnicas

### Dependencias

- **openpyxl**: Para leer/escribir archivos Excel
- **Django**: Framework web
- **Bootstrap 5**: Para UI (dropdowns requieren JS)

### Migraciones

- `0002_alter_catalogo_and_add_ratio_tag.py`: Migración que:
  - Elimina `anio_catalogo` de `Catalogo`
  - Cambia `empresa` a `OneToOneField`
  - Añade `fecha_creacion` y `fecha_actualizacion`
  - Cambia `naturaleza` a strings completos
  - Añade `bg_bloque`, `er_bloque` y `ratio_tag` a `Cuenta`

### Tests

- `test/test_excel_validation.py`: Test de validación de Excel
- `test/test_plantilla_generation.py`: Test de generación de plantillas

---

## Conclusión

El módulo de catálogo proporciona un sistema completo y robusto para gestionar cuentas contables y estados financieros. Su diseño enfocado en Excel, con plantillas inteligentes y validación flexible, facilita la carga de datos mientras mantiene la integridad y consistencia de la información financiera.

