from django import forms
from django.forms import ModelForm,TextInput, EmailInput, NumberInput, Select
from stela.models import Empresa
from stela.models.ciiu import Ciiu

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
            'telefono': TextInput(attrs={'class': 'form-control', 'maxlength': 9}),
            'nit': TextInput(attrs={'class': 'form-control', 'maxlength': 17}),
            'nrc': TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
            'ciiu': Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el queryset de ciiu esté disponible
        self.fields['ciiu'].queryset = Ciiu.objects.all().order_by('codigo')
        self.fields['ciiu'].empty_label = "--- Seleccione un código CIIU ---"
        self.fields['ciiu'].required = True
    
    def clean_ciiu(self):
        ciiu = self.cleaned_data.get('ciiu')
        if not ciiu:
            raise forms.ValidationError('El código CIIU es obligatorio')
        return ciiu


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

