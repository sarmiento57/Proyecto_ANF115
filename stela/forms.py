from django import forms
from stela.models.ciiu import Ciiu


class CiiuForm(forms.ModelForm):
    """
    Formulario para crear y editar códigos CIIU.
    Maneja la relación jerárquica padre-hijo.
    """
    
    class Meta:
        model = Ciiu
        fields = ['codigo', 'descripcion', 'nivel', 'padre']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'placeholder': 'Ej: 0111'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '255',
                'placeholder': 'Descripción del código CIIU'
            }),
            'nivel': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '6'
            }),
            'padre': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'codigo': 'Código',
            'descripcion': 'Descripción',
            'nivel': 'Nivel',
            'padre': 'Código Padre'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar el queryset de padre para excluir el mismo objeto si está editando
        if self.instance and self.instance.pk:
            self.fields['padre'].queryset = Ciiu.objects.exclude(
                codigo=self.instance.codigo
            )
        else:
            self.fields['padre'].queryset = Ciiu.objects.all()
        
        # Hacer el campo padre opcional
        self.fields['padre'].required = False
        self.fields['padre'].empty_label = "--- Sin padre (raíz) ---"
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if not codigo:
            raise forms.ValidationError('El código es obligatorio')
        
        # Si está editando, permitir el mismo código
        if self.instance and self.instance.pk:
            if Ciiu.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Este código CIIU ya existe')
        else:
            if Ciiu.objects.filter(codigo=codigo).exists():
                raise forms.ValidationError('Este código CIIU ya existe')
        
        return codigo
    
    def clean_nivel(self):
        nivel = self.cleaned_data.get('nivel')
        if nivel is None:
            raise forms.ValidationError('El nivel es obligatorio')
        if nivel < 1 or nivel > 6:
            raise forms.ValidationError('El nivel debe estar entre 1 y 6')
        return nivel
    
    def clean(self):
        cleaned_data = super().clean()
        padre = cleaned_data.get('padre')
        nivel = cleaned_data.get('nivel')
        
        # Validar que el nivel del hijo sea mayor que el del padre
        if padre and nivel:
            if nivel <= padre.nivel:
                raise forms.ValidationError(
                    f'El nivel del código hijo ({nivel}) debe ser mayor que el nivel del padre ({padre.nivel})'
                )
        
        return cleaned_data


