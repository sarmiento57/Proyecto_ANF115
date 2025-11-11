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
            #se cambio por el nuevo campo many to many
            self.fields['empresa'].queryset = Empresa.objects.filter(usuario=user).distinct()


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
            #se cambio por el nuevo campo many to many
            self.fields['empresa'].queryset = Empresa.objects.filter(usuario=user).distinct()


class MapeoCuentaForm(forms.Form):
    """Formulario dinámico para mapear cuentas a líneas de estado.
    
    Permite seleccionar MÚLTIPLES cuentas por cada línea de estado,
    ya que varias cuentas pueden contribuir al mismo concepto financiero.
    
    Solo muestra las líneas de estado requeridas para los ratios esenciales:
    - TOTAL_ACTIVO, ACTIVO_CORRIENTE, PASIVO_CORRIENTE (Balance)
    - VENTAS_NETAS, UTILIDAD_NETA (Resultados)
    """
    
    def __init__(self, *args, **kwargs):
        catalogo = kwargs.pop('catalogo', None)
        super().__init__(*args, **kwargs)
        
        if catalogo:
            # Líneas de estado requeridas para los ratios esenciales
            # Para Balance:
            lineas_balance = [
                'TOTAL_ACTIVO',
                'ACTIVO_CORRIENTE',
                'PASIVO_CORRIENTE',
            ]
            
            # Para Resultados: todas las líneas que componen UTILIDAD_NETA
            # UTILIDAD_NETA no se incluye porque se calcula automáticamente desde estas
            lineas_resultados = [
                'VENTAS_NETAS',
                'COSTO_NETO_VENTAS',  # Puede ser COSTO_VENTAS o COSTO_NETO_VENTAS
                'GASTOS_OPERATIVOS',
                'GASTO_FINANCIERO',
                'OTROS_INGRESOS',
                'OTROS_GASTOS',
                'IMPUESTO_SOBRE_LA_RENTA',
            ]
            
            # Crear líneas de estado que no existan
            nombres_lineas = {
                'COSTO_NETO_VENTAS': 'Costo Neto de Ventas',
                'GASTOS_OPERATIVOS': 'Gastos Operativos',
                'GASTO_FINANCIERO': 'Gasto Financiero',
                'OTROS_INGRESOS': 'Otros Ingresos',
                'OTROS_GASTOS': 'Otros Gastos',
                'IMPUESTO_SOBRE_LA_RENTA': 'Impuesto sobre la Renta',
            }
            
            for clave in lineas_resultados:
                if clave not in ['VENTAS_NETAS']:  # VENTAS_NETAS ya existe
                    LineaEstado.objects.get_or_create(
                        clave=clave,
                        estado='RES',
                        defaults={
                            'nombre': nombres_lineas.get(clave, clave.replace('_', ' ').title()),
                            'base_vertical': False
                        }
                    )
            
            # También verificar si existe COSTO_VENTAS (puede ser el nombre alternativo)
            # Si existe COSTO_VENTAS pero no COSTO_NETO_VENTAS, usar COSTO_VENTAS
            if not LineaEstado.objects.filter(clave='COSTO_NETO_VENTAS').exists():
                if LineaEstado.objects.filter(clave='COSTO_VENTAS').exists():
                    # Usar COSTO_VENTAS en lugar de COSTO_NETO_VENTAS
                    lineas_resultados = [l if l != 'COSTO_NETO_VENTAS' else 'COSTO_VENTAS' for l in lineas_resultados]
            
            # Obtener todas las líneas requeridas
            lineas_requeridas = lineas_balance + lineas_resultados
            lineas = LineaEstado.objects.filter(clave__in=lineas_requeridas).order_by('estado', 'clave')
            
            # Obtener todas las cuentas del catálogo con información de grupo y naturaleza
            cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo).select_related('grupo').order_by('codigo')
            
            # Crear un campo de selección múltiple para cada línea de estado requerida
            for linea in lineas:
                field_name = f'linea_{linea.clave}'
                
                # Determinar cuentas pre-seleccionadas basándose en:
                # 1. Mapeos existentes (prioridad)
                # 2. ratio_tag
                # 3. bg_bloque (para líneas de Balance)
                # 4. er_bloque (para líneas de Resultados)
                
                cuentas_preseleccionadas = set()
                
                # 1. Mapeos existentes
                mapeos_existentes = MapeoCuentaLinea.objects.filter(
                    linea=linea,
                    cuenta__grupo__catalogo=catalogo
                ).values_list('cuenta_id', flat=True)
                cuentas_preseleccionadas.update(mapeos_existentes)
                
                # 2. Por ratio_tag
                if linea.clave in ['TOTAL_ACTIVO', 'ACTIVO_CORRIENTE', 'PASIVO_CORRIENTE', 'VENTAS_NETAS']:
                    cuentas_por_tag = cuentas.filter(
                        ratio_tag=linea.clave
                    ).values_list('id_cuenta', flat=True)
                    cuentas_preseleccionadas.update(cuentas_por_tag)
                
                # 3. Por bg_bloque (para líneas de Balance)
                if linea.estado == 'BAL':
                    if linea.clave == 'ACTIVO_CORRIENTE':
                        cuentas_por_bloque = cuentas.filter(
                            bg_bloque='ACTIVO_CORRIENTE'
                        ).values_list('id_cuenta', flat=True)
                        cuentas_preseleccionadas.update(cuentas_por_bloque)
                    elif linea.clave == 'PASIVO_CORRIENTE':
                        cuentas_por_bloque = cuentas.filter(
                            bg_bloque='PASIVO_CORRIENTE'
                        ).values_list('id_cuenta', flat=True)
                        cuentas_preseleccionadas.update(cuentas_por_bloque)
                    elif linea.clave == 'TOTAL_ACTIVO':
                        # TOTAL_ACTIVO: todas las cuentas de activo
                        cuentas_activo = cuentas.filter(
                            grupo__naturaleza='Activo',
                            bg_bloque__in=['ACTIVO_CORRIENTE', 'ACTIVO_NO_CORRIENTE']
                        ).values_list('id_cuenta', flat=True)
                        cuentas_preseleccionadas.update(cuentas_activo)
                
                # 4. Por er_bloque (para líneas de Resultados)
                if linea.estado == 'RES':
                    # Mapear según er_bloque de las cuentas
                    # Mapeo de claves de línea a bloques er_bloque
                    mapeo_bloques = {
                        'VENTAS_NETAS': 'VENTAS_NETAS',
                        'COSTO_VENTAS': 'COSTO_NETO_VENTAS',  # COSTO_VENTAS mapea a COSTO_NETO_VENTAS
                        'COSTO_NETO_VENTAS': 'COSTO_NETO_VENTAS',
                        'GASTOS_OPERATIVOS': 'GASTOS_OPERATIVOS',
                        'GASTO_FINANCIERO': 'GASTO_FINANCIERO',
                        'OTROS_INGRESOS': 'OTROS_INGRESOS',
                        'OTROS_GASTOS': 'OTROS_GASTOS',
                        'IMPUESTO_SOBRE_LA_RENTA': 'IMPUESTO_SOBRE_LA_RENTA',
                    }
                    
                    bloque_er = mapeo_bloques.get(linea.clave)
                    if bloque_er:
                        cuentas_por_bloque = cuentas.filter(
                            er_bloque=bloque_er
                        ).values_list('id_cuenta', flat=True)
                        cuentas_preseleccionadas.update(cuentas_por_bloque)
                
                self.fields[field_name] = forms.ModelMultipleChoiceField(
                    queryset=cuentas,
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'class': 'form-check-input'
                    }),
                    label=f"{linea.nombre} ({linea.get_estado_display()})",
                    required=False,
                    help_text=f"Selecciona todas las cuentas que componen {linea.nombre}"
                )
                
                # Establecer valores iniciales
                if cuentas_preseleccionadas:
                    self.fields[field_name].initial = list(cuentas_preseleccionadas)


# Importar formularios desde el subdirectorio forms
from stela.forms.EmpresaForm import (
    EmpresaForm,
    EmpresaEditForm
)
