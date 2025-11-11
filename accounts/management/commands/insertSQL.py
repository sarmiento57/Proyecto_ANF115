from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Ejecuta un archivo SQL sin importar qué base de datos esté configurada en settings.py.'

    def handle(self, *args, **kwargs):
        # Ruta del archivo SQL
        sql_path = os.path.join('accounts', 'sql', 'sqlitePruebas.sql')

        if not os.path.exists(sql_path):
            self.stdout.write(self.style.ERROR(f"Archivo SQL no encontrado: {sql_path}"))
            return

        self.stdout.write(self.style.WARNING(f"Ejecutando script SQL desde: {sql_path}"))

        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # Conexión directa a la BD actual
            with connection.cursor() as cursor:
                # Desactivar validación de claves foráneas temporalmente
                cursor.execute("PRAGMA foreign_keys = OFF;")

                # Ejecutar cada sentencia individualmente
                insertados = 0
                errores = 0
                for statement in sql.split(';'):
                    stmt = statement.strip()
                    # Ignorar comentarios y líneas vacías
                    if stmt and not stmt.startswith('--'):
                        try:
                            # Reemplazar INSERT INTO con INSERT OR IGNORE INTO para evitar duplicados
                            if stmt.upper().startswith('INSERT INTO'):
                                stmt = stmt.replace('INSERT INTO', 'INSERT OR IGNORE INTO', 1)
                            cursor.execute(stmt)
                            if cursor.rowcount > 0:
                                insertados += cursor.rowcount
                        except Exception as e:
                            # Solo mostrar errores que no sean de duplicados
                            if 'UNIQUE constraint' not in str(e) and 'duplicate' not in str(e).lower():
                                self.stdout.write(self.style.WARNING(f"Advertencia en sentencia: {str(e)[:100]}"))
                            errores += 1

                # Reactivar las claves foráneas
                cursor.execute("PRAGMA foreign_keys = ON;")

            if insertados > 0:
                self.stdout.write(self.style.SUCCESS(f"Datos insertados: {insertados} registros. Errores ignorados (duplicados): {errores}"))
            else:
                self.stdout.write(self.style.WARNING(f"No se insertaron nuevos registros (posiblemente ya existen). Errores ignorados: {errores}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al ejecutar el script SQL: {e}"))
