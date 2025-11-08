from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.forms import PerfilEditForm

User = get_user_model()


class PerfilUsuarioTests(TestCase):
    """Tests para el perfil de usuario"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            telephone='1234-5678',
            dui='12345678-9'
        )
        
        # Crear otro usuario
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            email='other@example.com',
            first_name='Other',
            last_name='User'
        )
        
        # Crear cliente de prueba
        self.client = Client()
    
    def test_perfil_view_requires_login(self):
        """Test que ver perfil requiere login"""
        response = self.client.get(reverse('perfil_view'))
        self.assertEqual(response.status_code, 302)  # Redirige al login
    
    def test_perfil_view_with_login(self):
        """Test que ver perfil funciona con login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('perfil_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mi Perfil')
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)
        self.assertContains(response, self.user.email)
    
    def test_perfil_edit_requires_login(self):
        """Test que editar perfil requiere login"""
        response = self.client.get(reverse('perfil_edit'))
        self.assertEqual(response.status_code, 302)  # Redirige al login
    
    def test_perfil_edit_with_login(self):
        """Test que editar perfil funciona con login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('perfil_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Perfil')
        self.assertContains(response, self.user.username)
    
    def test_perfil_edit_post(self):
        """Test actualizar perfil"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Test Actualizado',
            'last_name': 'User Actualizado',
            'email': 'test_actualizado@example.com',
            'telephone': '8765-4321'
        }
        response = self.client.post(reverse('perfil_edit'), data)
        self.assertEqual(response.status_code, 302)  # Redirige después de actualizar
        
        # Verificar que se actualizó
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test Actualizado')
        self.assertEqual(self.user.last_name, 'User Actualizado')
        self.assertEqual(self.user.email, 'test_actualizado@example.com')
        self.assertEqual(self.user.telephone, '8765-4321')
    
    def test_perfil_edit_cannot_change_username(self):
        """Test que no se puede cambiar el username"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'telephone': '1234-5678'
        }
        response = self.client.post(reverse('perfil_edit'), data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el username no cambió
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')
    
    def test_perfil_edit_cannot_change_dui(self):
        """Test que no se puede cambiar el DUI"""
        original_dui = self.user.dui
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'telephone': '1234-5678'
        }
        response = self.client.post(reverse('perfil_edit'), data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el DUI no cambió
        self.user.refresh_from_db()
        self.assertEqual(self.user.dui, original_dui)
    
    def test_perfil_edit_duplicate_email(self):
        """Test que no se puede usar un email ya registrado"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': self.other_user.email,  # Email de otro usuario
            'telephone': '1234-5678'
        }
        response = self.client.post(reverse('perfil_edit'), data)
        self.assertEqual(response.status_code, 200)  # Muestra errores
        self.assertContains(response, 'ya está registrado')


class PerfilEditFormTests(TestCase):
    """Tests para el formulario de edición de perfil"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            telephone='1234-5678'
        )
    
    def test_form_valid(self):
        """Test formulario válido"""
        form = PerfilEditForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'telephone': '1234-5678'
        }, instance=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_telephone_format(self):
        """Test que valida el formato de teléfono"""
        form = PerfilEditForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'telephone': '12345678'  # Formato incorrecto
        }, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('telephone', form.errors)
    
    def test_form_invalid_name_with_numbers(self):
        """Test que valida que los nombres solo tengan letras"""
        form = PerfilEditForm(data={
            'first_name': 'Test123',  # Tiene números
            'last_name': 'User',
            'email': 'test@example.com',
            'telephone': '1234-5678'
        }, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
    
    def test_form_duplicate_email(self):
        """Test que no acepta email duplicado"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            email='other@example.com'
        )
        
        form = PerfilEditForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'other@example.com',  # Email de otro usuario
            'telephone': '1234-5678'
        }, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_save(self):
        """Test que el formulario guarda correctamente"""
        form = PerfilEditForm(data={
            'first_name': 'Test Actualizado',
            'last_name': 'User Actualizado',
            'email': 'test_actualizado@example.com',
            'telephone': '8765-4321'
        }, instance=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test Actualizado')
        self.assertEqual(self.user.last_name, 'User Actualizado')
        self.assertEqual(self.user.email, 'test_actualizado@example.com')
        self.assertEqual(self.user.telephone, '8765-4321')
