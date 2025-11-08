from django import forms
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class PerfilEditForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario.
    Solo permite editar: first_name, last_name, telephone, email
    NO permite cambiar: username, dui
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
                'title': 'Solo letras y espacios'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
                'title': 'Solo letras y espacios'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '\\d{4}-\\d{4}',
                'placeholder': '####-####',
                'title': 'Formato: ####-####'
            }),
        }
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'telephone': 'Teléfono',
        }
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError('El nombre es obligatorio')
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', first_name):
            raise forms.ValidationError('El nombre solo debe contener letras y espacios')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError('El apellido es obligatorio')
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', last_name):
            raise forms.ValidationError('El apellido solo debe contener letras y espacios')
        return last_name
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError('El correo electrónico es obligatorio')
        
        # Verificar que el email no esté en uso por otro usuario
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado')
        return email
    
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone', '').strip()
        if telephone:  # Teléfono es opcional
            if not re.match(r'^\d{4}-\d{4}$', telephone):
                raise forms.ValidationError('El número de teléfono debe tener el formato ####-####')
        return telephone
