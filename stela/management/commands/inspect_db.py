"""
Comando para inspeccionar la estructura de la base de datos
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Inspecciona la estructura de las tablas en la base de datos"

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write("TABLAS EN LA BASE DE DATOS")
        self.stdout.write("=" * 80)
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'):
                continue
                
            self.stdout.write(f"\n📋 Tabla: {table_name}")
            self.stdout.write("-" * 80)
            
            # Obtener información de columnas
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            self.stdout.write(f"{'Columna':<30} {'Tipo':<20} {'Null':<8} {'Default':<15} {'PK'}")
            self.stdout.write("-" * 80)
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                null_str = "NO" if not_null else "YES"
                pk_str = "✓" if is_pk else ""
                default_str = str(default_val) if default_val else ""
                
                self.stdout.write(f"{col_name:<30} {col_type:<20} {null_str:<8} {default_str:<15} {pk_str}")
            
            # Obtener número de registros
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                self.stdout.write(f"\n  Total de registros: {count}")
            except:
                pass
            
            # Si es stela_empresa, mostrar datos problemáticos
            if table_name == 'stela_empresa':
                self.stdout.write("\n🔍 Verificando datos en stela_empresa:")
                cursor.execute("SELECT nit, razon_social, idCiiu_id FROM stela_empresa")
                empresas = cursor.fetchall()
                for emp in empresas:
                    self.stdout.write(f"  NIT: {emp[0]}, Razón: {emp[1]}, CIIU: {emp[2]}")
        
        self.stdout.write("\n" + "=" * 80)

