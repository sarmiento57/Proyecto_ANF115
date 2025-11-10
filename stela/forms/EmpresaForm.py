from django.forms import ModelForm,TextInput, EmailInput, NumberInput
from stela.models import Empresa

class EmpresaForm(ModelForm):
    class Meta:
        model = Empresa
        fields = ["razon_social","direccion","email","telefono","nit","nrc","ciiu"]

        labels ={
            'razon_social':'Nombre legal de la empresa',
            'direccion':'Dirección de la empresa',
            'nit': 'NIT (Identificador Tributario)',
            'nrc': 'NRC (Numero de registro de contribuyente)',
            'telefono':'Teléfono de la empresa',
            'ciiu': 'CIIU Clasificación Industrial Internacional Uniforme'
        }

        widgets = {
            'razon_social': TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social Completa'}),
            'direccion':TextInput(attrs={'class': 'form-control', 'maxlength':255, 'placeholder':'Departamento,Distrito,Municipio, etc.'}),
            'email': EmailInput(attrs={'class': 'form-control','placeholder': 'correo@dominio.com'}),
            'telefono': TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
            'nit': TextInput(attrs={'class': 'form-control', 'maxlength': 14}),
            'nrc': TextInput(attrs={'class': 'form-control', 'maxlength': 8}),

        }


class EmpresaEditForm(ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'razon_social',
            'direccion',
            'ciiu',
            'email',
            'telefono'
        ]

        labels = {
            'razon_social': 'Nombre legal de la empresa',
            'direccion': 'Dirección de la empresa',
            'telefono': 'Teléfono de la empresa',
            'ciiu': 'CIIU Clasificación Industrial Internacional Uniforme'

        }

        widgets = {
            'razon_social': TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social Completa'}),
            'direccion': TextInput(attrs={'class': 'form-control', 'maxlength': 255,
            'placeholder': 'Departamento,Distrito,Municipio, etc.'}),
            'email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@dominio.com'}),
            'telefono': TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
        }

