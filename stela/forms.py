from django import forms
from stela.models.ciiu import Ciiu
from stela.models.empresa import Empresa
from stela.models.catalogo import Catalogo, Cuenta
from stela.models.finanzas import LineaEstado, MapeoCuentaLinea


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


class CatalogoUploadForm(forms.Form):
    """Formulario para subir catálogo desde CSV"""
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Empresa',
        required=True
    )
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        label='Archivo CSV/Excel',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['empresa'].queryset = Empresa.objects.filter(usuario=user)


class CatalogoManualForm(forms.Form):
    """Formulario para crear catálogo manualmente"""
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Empresa',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['empresa'].queryset = Empresa.objects.filter(usuario=user)


class MapeoCuentaForm(forms.Form):
    """Formulario dinámico para mapear cuentas a líneas de estado"""
    
    def __init__(self, *args, **kwargs):
        catalogo = kwargs.pop('catalogo', None)
        super().__init__(*args, **kwargs)
        
        if catalogo:
            # Obtener todas las líneas de estado
            lineas = LineaEstado.objects.all().order_by('estado', 'clave')
            
            # Obtener todas las cuentas del catálogo
            cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo).order_by('codigo')
            
            # Crear un campo select para cada línea de estado
            for linea in lineas:
                field_name = f'linea_{linea.clave}'
                self.fields[field_name] = forms.ModelChoiceField(
                    queryset=cuentas,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    label=f"{linea.nombre} ({linea.get_estado_display()})",
                    required=False,
                    empty_label="-- Seleccione una cuenta --"
                )
                
                # Si ya existe un mapeo, establecer el valor inicial
                try:
                    mapeo = MapeoCuentaLinea.objects.filter(linea=linea).first()
                    if mapeo and mapeo.cuenta.grupo.catalogo == catalogo:
                        self.fields[field_name].initial = mapeo.cuenta
                except:
                    pass


