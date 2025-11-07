from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import messages
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
import os
from django.conf import settings
from stela.models.ciiu import Ciiu
from stela.models.empresa import Empresa
from accounts.models import OptionForm, UserAccess
from accounts.decorators import access_required

User = get_user_model()


class CiiuCRUDTests(TestCase):
    """Tests para el CRUD de códigos CIIU"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        
        # Crear opción de catálogos
        self.option_catalogos = OptionForm.objects.create(
            optionId='011',
            description='Catalogos',
            formNumber=1
        )
        
        # Dar acceso al usuario
        UserAccess.objects.create(
            userId=self.user,
            optionId=self.option_catalogos
        )
        
        # Crear cliente de prueba
        self.client = Client()
        
        # Crear códigos CIIU de prueba
        self.ciiu_padre = Ciiu.objects.create(
            codigo='A',
            descripcion='Actividad A',
            nivel=1,
            padre=None
        )
        
        self.ciiu_hijo = Ciiu.objects.create(
            codigo='01',
            descripcion='Actividad 01',
            nivel=2,
            padre=self.ciiu_padre
        )
    
    def test_ciiu_list_requires_login(self):
        """Test que el listado requiere login"""
        response = self.client.get(reverse('ciiu_list'))
        self.assertEqual(response.status_code, 302)  # Redirige al login
    
    def test_ciiu_list_requires_access(self):
        """Test que el listado requiere acceso a catálogos"""
        # Login sin acceso
        user_no_access = User.objects.create_user(
            username='noaccess',
            password='testpass123'
        )
        self.client.login(username='noaccess', password='testpass123')
        
        response = self.client.get(reverse('ciiu_list'))
        self.assertEqual(response.status_code, 302)  # Redirige
    
    def test_ciiu_list_with_access(self):
        """Test que el listado funciona con acceso"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ciiu_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Catálogos CIIU')
        self.assertContains(response, self.ciiu_padre.codigo)
    
    def test_ciiu_list_search(self):
        """Test búsqueda en el listado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ciiu_list'), {'q': 'A'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ciiu_padre.codigo)
    
    def test_ciiu_create_requires_access(self):
        """Test que crear requiere acceso"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ciiu_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Código CIIU')
    
    def test_ciiu_create_post(self):
        """Test crear código CIIU"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'codigo': '02',
            'descripcion': 'Actividad 02',
            'nivel': 2,
            'padre': self.ciiu_padre.codigo
        }
        response = self.client.post(reverse('ciiu_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirige después de crear
        self.assertTrue(Ciiu.objects.filter(codigo='02').exists())
    
    def test_ciiu_create_duplicate_code(self):
        """Test que no se puede crear código duplicado"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'codigo': 'A',  # Ya existe
            'descripcion': 'Nueva descripción',
            'nivel': 1
        }
        response = self.client.post(reverse('ciiu_create'), data)
        self.assertEqual(response.status_code, 200)  # Muestra errores
        self.assertContains(response, 'ya existe')
    
    def test_ciiu_update_requires_access(self):
        """Test que editar requiere acceso"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ciiu_update', args=[self.ciiu_padre.codigo]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Código CIIU')
    
    def test_ciiu_update_post(self):
        """Test actualizar código CIIU"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'codigo': self.ciiu_padre.codigo,
            'descripcion': 'Descripción actualizada',
            'nivel': self.ciiu_padre.nivel,
            'padre': ''
        }
        response = self.client.post(
            reverse('ciiu_update', args=[self.ciiu_padre.codigo]),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirige después de actualizar
        self.ciiu_padre.refresh_from_db()
        self.assertEqual(self.ciiu_padre.descripcion, 'Descripción actualizada')
    
    def test_ciiu_delete_requires_access(self):
        """Test que eliminar requiere acceso"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ciiu_delete', args=[self.ciiu_padre.codigo]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Eliminar Código CIIU')
    
    def test_ciiu_delete_with_empresas(self):
        """Test que no se puede eliminar si tiene empresas asociadas"""
        # Crear empresa asociada
        empresa = Empresa.objects.create(
            nit='0614-123456-101-5',
            razon_social='Empresa Test',
            nrc='12345678',
            direccion='Dirección Test',
            telefono='1234-5678',
            email='empresa@test.com',
            idCiiu=self.ciiu_padre,
            usuario=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('ciiu_delete', args=[self.ciiu_padre.codigo]))
        self.assertEqual(response.status_code, 302)  # Redirige con error
        self.assertTrue(Ciiu.objects.filter(codigo=self.ciiu_padre.codigo).exists())
    
    def test_ciiu_delete_with_hijos(self):
        """Test que no se puede eliminar si tiene hijos"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('ciiu_delete', args=[self.ciiu_padre.codigo]))
        self.assertEqual(response.status_code, 302)  # Redirige con error
        self.assertTrue(Ciiu.objects.filter(codigo=self.ciiu_padre.codigo).exists())
    
    def test_ciiu_delete_success(self):
        """Test eliminar código CIIU sin empresas ni hijos"""
        # Crear código sin hijos ni empresas
        ciiu_solo = Ciiu.objects.create(
            codigo='99',
            descripcion='Código solo',
            nivel=1
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('ciiu_delete', args=[ciiu_solo.codigo]))
        self.assertEqual(response.status_code, 302)  # Redirige después de eliminar
        self.assertFalse(Ciiu.objects.filter(codigo='99').exists())


class CiiuFormTests(TestCase):
    """Tests para el formulario CIIU"""
    
    def setUp(self):
        self.ciiu_padre = Ciiu.objects.create(
            codigo='A',
            descripcion='Actividad A',
            nivel=1
        )
    
    def test_form_valid(self):
        """Test formulario válido"""
        from stela.forms import CiiuForm
        form = CiiuForm(data={
            'codigo': '01',
            'descripcion': 'Actividad 01',
            'nivel': 2,
            'padre': self.ciiu_padre.codigo
        })
        self.assertTrue(form.is_valid())
    
    def test_form_duplicate_code(self):
        """Test que no acepta código duplicado"""
        from stela.forms import CiiuForm
        form = CiiuForm(data={
            'codigo': 'A',  # Ya existe
            'descripcion': 'Nueva',
            'nivel': 1
        })
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)
    
    def test_form_invalid_nivel(self):
        """Test que valida el nivel"""
        from stela.forms import CiiuForm
        form = CiiuForm(data={
            'codigo': '02',
            'descripcion': 'Actividad',
            'nivel': 7  # Nivel inválido (>6)
        })
        self.assertFalse(form.is_valid())
    
    def test_form_hijo_nivel_mayor(self):
        """Test que el hijo debe tener nivel mayor que el padre"""
        from stela.forms import CiiuForm
        form = CiiuForm(data={
            'codigo': '01',
            'descripcion': 'Actividad',
            'nivel': 1,  # Mismo nivel que padre
            'padre': self.ciiu_padre.codigo
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class SeedCiiuCommandTests(TestCase):
    """Tests para el comando seed_ciiu"""
    
    def test_seed_ciiu_command_exists(self):
        """Test que el comando existe"""
        try:
            # El comando --help puede salir con SystemExit, eso es normal
            try:
                call_command('seed_ciiu', '--help')
            except SystemExit:
                pass  # Es normal que --help salga con SystemExit
        except CommandError:
            self.fail("El comando seed_ciiu no existe")
    
    def test_seed_ciiu_loads_data(self):
        """Test que el comando carga datos desde CSV"""
        # Verificar que el archivo CSV existe
        csv_path = os.path.join(
            settings.BASE_DIR,
            'stela',
            'seeders',
            'ciiu.csv'
        )
        self.assertTrue(os.path.exists(csv_path), f"El archivo {csv_path} no existe")
        
        # Ejecutar el comando
        out = StringIO()
        try:
            call_command('seed_ciiu', stdout=out)
        except Exception as e:
            self.fail(f"El comando falló: {e}")
        
        # Verificar que se cargaron datos
        self.assertGreater(Ciiu.objects.count(), 0, "No se cargaron códigos CIIU")
        
        # Verificar que hay códigos con padre
        ciiu_con_padre = Ciiu.objects.exclude(padre=None)
        self.assertGreater(ciiu_con_padre.count(), 0, "No se cargaron códigos con padre")
    
    def test_seed_ciiu_creates_hierarchy(self):
        """Test que el comando crea la jerarquía correctamente"""
        out = StringIO()
        call_command('seed_ciiu', stdout=out)
        
        # Buscar un código que debería tener padre
        ciiu_hijo = Ciiu.objects.filter(codigo='55').first()
        if ciiu_hijo:
            self.assertIsNotNone(ciiu_hijo.padre, "El código 55 debería tener padre")
            self.assertEqual(ciiu_hijo.padre.codigo, 'I', "El padre de 55 debería ser I")
