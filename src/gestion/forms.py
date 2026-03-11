from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Maquinaria, Usuario, Checklist, OrdenTrabajo, CompraCombustible, CombustibleLog, OrdenTaller, Empresa, ConfiguracionMantencion
import re

def validar_rut_chileno(rut_str):
    if not rut_str: return False
    rut_str = rut_str.replace('.', '').replace('-', '').upper()
    if len(rut_str) < 2 or not rut_str[:-1].isdigit():
        return False
    rut_num = rut_str[:-1]
    dv_dado = rut_str[-1]
    suma = 0
    multiplo = 2
    for c in reversed(rut_num):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
    esperado = 11 - (suma % 11)
    dv_esp = '0' if esperado == 11 else 'K' if esperado == 10 else str(esperado)
    return dv_dado == dv_esp

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nombre_fantasia', 'rut_empresa', 'usa_despachador',
            'modulo_mantencion', 'modulo_checklist', 'modulo_combustible', 
            'modulo_gps', 'modulo_reporteria'
        ]
        labels = {
            'nombre_fantasia': 'Nombre de Fantasía o Razón Social',
            'rut_empresa': 'RUT Empresa',
            'usa_despachador': 'Utiliza rol Despachador (Checklists extra)',
            'modulo_mantencion': 'Módulo de Mantención y Taller Mecánico',
            'modulo_checklist': 'Módulo de Inspección Diaria (Checklists)',
            'modulo_combustible': 'Módulo de Gestión de Combustible',
            'modulo_gps': 'Tracking GPS y Telemétrica',
            'modulo_reporteria': 'Centro de Reportes y Descargas PDF',
        }
        widgets = {
            'nombre_fantasia': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Constructora ABC'}),
            'rut_empresa': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 76.543.210-K'}),
            'usa_despachador': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'modulo_mantencion': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'modulo_checklist': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'modulo_combustible': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'modulo_gps': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'modulo_reporteria': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_rut_empresa(self):
        rut = self.cleaned_data.get('rut_empresa')
        if rut:
            if not validar_rut_chileno(rut):
                raise forms.ValidationError('El RUT de la empresa ingresado no es válido matemáticamente.')
        return rut

class ConfiguracionMantencionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionMantencion
        fields = ['intervalo_horas', 'intervalo_km']
        labels = {
            'intervalo_horas': 'Intervalo de Mantención Preventiva (Horas)',
            'intervalo_km': 'Intervalo de Mantención Preventiva (Km)'
        }
        widgets = {
            'intervalo_horas': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'min': '1', 'placeholder': 'Ej. 200'}),
            'intervalo_km': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'min': '1', 'placeholder': 'Ej. 10000'})
        }

class MaquinariaForm(forms.ModelForm):
    class Meta:
        model = Maquinaria
        # Excluimos empresa porque lo definiremos internamente en la Vista
        exclude = ['empresa']
        labels = {
            'id_interno': 'ID Interno o Número Máquina',
            'tipo': 'Tipo de Máquina',
            'unidad_medida': 'Unidad Control',
            'valor_actual_medida': 'Horómetro o Km Actual',
        }
        widgets = {
            'id_interno': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: EX-01'}),
            'patente': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: ABCD12', 'pattern': '[A-Za-z0-9]{6}', 'title': 'Formato todo junto, Ej: ABCD12', 'maxlength': '6'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'marca': forms.TextInput(attrs={'class': 'form-input'}),
            'modelo': forms.TextInput(attrs={'class': 'form-input'}),
            'tonelaje': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': '(Indique en toneladas)'}),
            'tipo_combustible': forms.Select(choices=[('DIESEL', 'Diésel'), ('GASOLINA', 'Gasolina'), ('ELECTRICA', 'Eléctrica')], attrs={'class': 'form-input'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-input'}),
            'valor_actual_medida': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'consumo_teorico': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'proximo_mantenimiento': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'estado': forms.Select(attrs={'class': 'form-input'}),
            'operador_asignado': forms.Select(attrs={'class': 'form-input'}),
        }

    def clean_patente(self):
        import re
        patente = self.cleaned_data.get('patente')
        if patente:
            patente = patente.upper().replace(' ', '').replace('-', '')
            if not re.match(r'^[A-Z0-9]{6}$', patente):
                raise forms.ValidationError('La patente debe tener el formato todo junto de 6 caracteres (Ej: ABCD12).')
        return patente

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        # Para CharField con choices, empty_label no aplica.
        # La solución correcta es prepend una tupla vacía al inicio de las choices.
        self.fields['unidad_medida'].choices = [
            ('', 'Seleccione Horas o Kilómetros')
        ] + list(Maquinaria.UNIDADES)
        
        if empresa:
            self.fields['operador_asignado'].queryset = Usuario.objects.filter(empresa=empresa, rol='OPERATOR')
        self.fields['operador_asignado'].empty_label = "Sin Operador Fijo (Opcional)"

class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'rut', 'nombre_completo', 'email', 'telefono', 'valor_hora')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: admin.empresa'}),
            'rut': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 12345678-9', 'pattern': '^[0-9]{7,8}-[0-9Kk]{1}$', 'title': 'Formato con guión: 12345678-9'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre completo (Nombres y Apellidos)'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Correo electrónico'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: +56912345678', 'pattern': '^\\+56[0-9]{9}$', 'title': 'Debe comensar con +56 seguido de 9 dígitos', 'value': '+56'}),
            'rol': forms.Select(attrs={'class': 'form-input'}),
            'estado': forms.Select(attrs={'class': 'form-input'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'Valor por hora ($)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los campos password1 y password2 vienen de UserCreationForm y no pasan por widgets del Meta,
        # por eso hay que decorarlos manualmente aquí.
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Contraseña temporal del cliente'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Repita la contraseña'
        })

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if rut:
            if not validar_rut_chileno(rut):
                raise forms.ValidationError('El RUT de usuario ingresado no es válido matemáticamente (Dígito Verificador incorrecto).')
        return rut

class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('rut', 'nombre_completo', 'email', 'telefono', 'rol', 'estado', 'valor_hora')
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-input', 'pattern': '^[0-9]{7,8}-[0-9Kk]{1}$', 'title': 'Formato con guión: 12345678-9'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'pattern': '^\+56[0-9]{9}$', 'title': 'Debe comensar con +56 seguido de 9 dígitos'}),
            'rol': forms.Select(attrs={'class': 'form-input'}),
            'estado': forms.Select(attrs={'class': 'form-input'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if rut:
            if not validar_rut_chileno(rut):
                raise forms.ValidationError('El RUT de usuario ingresado no es válido matemáticamente (Dígito Verificador incorrecto).')
        return rut

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['maquina', 'niveles_ok', 'luces_ok', 'estructura_ok', 'comentarios', 'firma_operador']
        widgets = {
            'maquina': forms.Select(attrs={'class': 'form-input'}),
            'niveles_ok': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'luces_ok': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'estructura_ok': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'comentarios': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Ej. Foco izquierdo quebrado, fuga de aceite mínima...'}),
            'firma_operador': forms.HiddenInput(attrs={'id': 'firma_operador'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            # Filtrar maquinarias que pertenezcan a la empresa y no estén en el taller
            self.fields['maquina'].queryset = Maquinaria.objects.filter(empresa=empresa).exclude(estado='TALLER')
            self.fields['maquina'].empty_label = "Seleccione una Máquina Operativa"

class OrdenTrabajoSalidaForm(forms.ModelForm):
    class Meta:
        model = OrdenTrabajo
        fields = ['maquina', 'operador', 'medida_salida', 'nro_guia_despacho']
        widgets = {
            'maquina': forms.Select(attrs={'class': 'form-input'}),
            'operador': forms.Select(attrs={'class': 'form-input'}),
            'medida_salida': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'Ej. 5200.5 (Horas/Km actuales)'}),
            'nro_guia_despacho': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. GD-10293'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            # IMPORTANTE: Usamos Maquinaria._default_manager para bypassear el
            # EmpresaManager (que ya filtra por empresa en el middleware).
            # Hacemos el filtro directo para evitar doble filtro en blanco.
            maquinas_disponibles = Maquinaria._default_manager.filter(
                empresa=empresa,
                estado__in=['DISPONIBLE']
            )
            self.fields['maquina'].queryset = maquinas_disponibles
            self.fields['maquina'].empty_label = "Seleccione Máquina en Patio"
            
            # Solo operadores activos (rol OPERATOR o DISPATCHER según la empresa)
            operadores = Usuario._default_manager.filter(
                empresa=empresa,
                rol__in=['OPERATOR', 'DISPATCHER'],
                estado='DISPONIBLE'
            )
            self.fields['operador'].queryset = operadores
            self.fields['operador'].empty_label = "Asignar a un Operador"

class OrdenTrabajoEntradaForm(forms.ModelForm):
    class Meta:
        model = OrdenTrabajo
        fields = ['medida_entrada']
        widgets = {
            'medida_entrada': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'Ej. 5210.5 (Horas/Km Finales)'}),
        }

class CompraCombustibleForm(forms.ModelForm):
    class Meta:
        model = CompraCombustible
        fields = ['fecha_compra', 'nro_factura', 'cantidad_litros', 'precio_litro', 'total_pago']
        widgets = {
            'fecha_compra': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'nro_factura': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'N° Factura o Documento'}),
            'cantidad_litros': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': '1000.00', 'id': 'cantidad_litros'}),
            'precio_litro': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'placeholder': 'Ej. 1020', 'id': 'precio_litro'}),
            'total_pago': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'placeholder': 'Ej. 1020500', 'id': 'total_pago'}),
        }

class CombustibleLogForm(forms.ModelForm):
    class Meta:
        model = CombustibleLog
        fields = ['tipo_carga', 'tipo_documento', 'numero_documento', 'orden_trabajo', 'maquina', 'operador', 'litros', 'precio_unitario', 'costo_total', 'medida_al_cargar', 'sello_flujometro']
        labels = {
            'precio_unitario': 'Precio Litro',
            'orden_trabajo': 'Orden de Trabajo (Opcional)',
            'sello_flujometro': 'Número de Sello',
        }
        widgets = {
            'tipo_carga': forms.Select(attrs={'class': 'form-input', 'id': 'tipo_carga_select'}),
            'tipo_documento': forms.TextInput(attrs={'class': 'form-input', 'id': 'tipo_documento_input', 'placeholder': 'Ej. Factura, Boleta (Sólo Externa)'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-input', 'id': 'numero_documento_input', 'placeholder': 'Ej. 12345'}),
            'orden_trabajo': forms.Select(attrs={'class': 'form-input'}),
            'maquina': forms.Select(attrs={'class': 'form-input'}),
            'operador': forms.Select(attrs={'class': 'form-input'}),
            'litros': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'id': 'litros_input', 'placeholder': 'Cantidad en Litros (Lts)'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'id': 'precio_unitario_input', 'placeholder': 'Dejar vacío si es INTERNA'}),
            'costo_total': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'id': 'costo_total_input', 'placeholder': 'Auto-calculado (Externa)'}),
            'medida_al_cargar': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'Horómetro/Km actual de la máquina'}),
            'sello_flujometro': forms.NumberInput(attrs={'class': 'form-input', 'id': 'sello_flujometro_input', 'placeholder': 'Obligatorio en Carga Interna'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['maquina'].queryset = Maquinaria.objects.filter(empresa=empresa)
            self.fields['maquina'].empty_label = "Seleccione Máquina"
            self.fields['operador'].queryset = Usuario.objects.filter(empresa=empresa, rol='OPERATOR')
            self.fields['operador'].empty_label = "Seleccione Operador"
            self.fields['orden_trabajo'].queryset = OrdenTrabajo.objects.filter(empresa=empresa).order_by('-id')
            self.fields['orden_trabajo'].empty_label = "Sin Orden Asignada"
        
        # Buscamos el último sello de flujómetro de la Empresa para validarlo
        self.ultimo_sello = None
        if empresa:
            ultimo_log = CombustibleLog.objects.filter(
                empresa=empresa, 
                tipo_carga='INTERNA', 
                sello_flujometro__isnull=False
            ).order_by('-id').first()
            
            if ultimo_log:
                self.ultimo_sello = ultimo_log.sello_flujometro
                self.fields['sello_flujometro'].widget.attrs['placeholder'] = f'Último Sello: {self.ultimo_sello}'
                self.fields['sello_flujometro'].help_text = f"El sello anterior fue: <strong>{self.ultimo_sello}</strong>. El nuevo sello debe ser un número mayor."
            else:
                self.fields['sello_flujometro'].help_text = "Ingrese el primer sello del mes."
                
        # Hacemos los campos de precio no requeridos porque se calculan en backend si la carga es INTERNA
        self.fields['precio_unitario'].required = False
        self.fields['costo_total'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_carga = cleaned_data.get('tipo_carga')
        sello_flujometro = cleaned_data.get('sello_flujometro')
        
        if tipo_carga == 'INTERNA':
            if sello_flujometro is None:
                self.add_error('sello_flujometro', "El Número de Sello es OBLIGATORIO para las Cargas Internas.")
            elif self.ultimo_sello is not None and sello_flujometro <= self.ultimo_sello:
                self.add_error('sello_flujometro', f"Error: El Número de Sello ({sello_flujometro}) debe ser MAYOR al último registrado ({self.ultimo_sello}).")
        
        return cleaned_data


class OrdenTallerForm(forms.ModelForm):
    class Meta:
        model = OrdenTaller
        fields = ['maquina', 'tipo_mantenimiento', 'medida_ingreso', 'descripcion_falla']
        widgets = {
            'maquina': forms.Select(attrs={'class': 'form-input'}),
            'tipo_mantenimiento': forms.Select(attrs={'class': 'form-input'}),
            'medida_ingreso': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'Horómetro o Km actual'}),
            'descripcion_falla': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Describa el motivo de ingreso o falla reportada...'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            # Filtramos máquinas para que no puedan ingresar al taller máquinas que YA están en el taller
            self.fields['maquina'].queryset = Maquinaria.objects.filter(empresa=empresa).exclude(estado='TALLER')
            self.fields['maquina'].empty_label = "Seleccione una Máquina"

class OrdenTallerCloseForm(forms.ModelForm):
    update_mantenimiento = forms.BooleanField(
        required=False,
        label="¿Actualizar Próximo Mantenimiento?",
        help_text="Si marca esta opción, el sistema avanzará el contador de próximo mantenimiento (recomendado en Preventivos)."
    )

    class Meta:
        model = OrdenTaller
        fields = ['trabajo_realizado', 'costo_total', 'medida_salida']
        labels = {
            'medida_salida': 'Horómetro/Km de Salida',
        }
        widgets = {
            'trabajo_realizado': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Detalle las reparaciones efectuadas y repuestos usados...'}),
            'costo_total': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'placeholder': 'Ej. 150000'}),
            'medida_salida': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'Horómetro/Km al entregar'}),
        }


class PerfilForm(forms.ModelForm):
    """
    Formulario que permite al usuario editar sus propios datos básicos.
    Excluye campos sensibles como rol, estado y empresa (solo editables por Admin).
    """
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono / Celular',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tu nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tu apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'correo@empresa.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+56 9 XXXX XXXX'}),
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Sincronizar nombre_completo con first_name + last_name
        usuario.nombre_completo = f"{usuario.first_name} {usuario.last_name}".strip()
        if commit:
            usuario.save()
        return usuario
