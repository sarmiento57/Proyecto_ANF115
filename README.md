# Proyecto de Análisis Financiero – ANF115 - FIA UES

Sistema web desarrollado con **Django** y **MySQL** para realizar análisis financiero de empresas, incluyendo cálculo de ratios, análisis horizontal y vertical, y generación de reportes gráficos.

---

## Descripción general

Este proyecto tiene como objetivo construir una aplicación web que permita:

- Registrar empresas y sus estados financieros (balances y resultados).
- Calcular ratios financieros automáticamente (liquidez, endeudamiento, rentabilidad, etc.).
- Comparar los resultados por año y con promedios sectoriales.
- Generar gráficos de evolución por tipo de ratio.
- Realizar proyecciones de ventas usando distintos métodos.
- Cargar datos desde Excel o ingresarlos manualmente.

---

## Instrucciones para implementar el proyecto

### 1 Configurar repositorio

```bash
# 1. Clonar el repositorio
git clone https://github.com/sarmiento57/Proyecto_ANF115.git
cd Proyecto_ANF115

# 2. Crear entorno virtual
py -m venv venv

# 3. Activar entorno virtual
venv\Scripts\activate
# (En Linux/Mac usar: source venv/bin/activate)

# 4. Instalar librerias
pip install -r requirements.txt

# 5. Aplicar migraciones
py manage.py makemigrations
py manage.py migrate

# 6. Iniciar el servidor local
py manage.py runserver

# 7. Abrir el navegador
# http://127.0.0.1:8000/
```
### 2 Insertar scripts SQL con datos iniciales

```markdown
# 1. Ejecutar el siguiente comando
py manage.py insertSQ


