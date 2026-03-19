from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .middleware import get_current_empresa

class EmpresaManager(models.Manager):
    """ Filtra automáticamente los querysets por la empresa actual en sesión """
    def get_queryset(self):
        qs = super().get_queryset()
        empresa_actual = get_current_empresa()
        if empresa_actual:
            return qs.filter(empresa=empresa_actual)
        return qs

class UsuarioManager(UserManager):
    """ Hereda de UserManager para mantener login (get_by_natural_key) y filtra por Empresa """
    def get_queryset(self):
        qs = super().get_queryset()
        empresa_actual = get_current_empresa()
        if empresa_actual:
            return qs.filter(empresa=empresa_actual)
        return qs

# 1. EMPRESAS
class Empresa(models.Model):
    nombre_fantasia = models.CharField(max_length=100)
    rut_empresa = models.CharField(max_length=20, unique=True)
    usa_despachador = models.BooleanField(default=False)
    activa = models.BooleanField(default=True, help_text="Soft Delete: Define si la empresa tiene acceso al sistema.")
    
    # --- FEATURE FLAGS SAAS (Modulos Contratados) ---
    modulo_mantencion = models.BooleanField(default=False, help_text="Taller y Mantenimiento")
    modulo_checklist = models.BooleanField(default=True, help_text="Inspecciones Diarias")
    modulo_combustible = models.BooleanField(default=False, help_text="Gestión y Cargas")
    modulo_gps = models.BooleanField(default=False, help_text="Rastreo Telemétrico")
    modulo_reporteria = models.BooleanField(default=False, help_text="Exportación a PDF/Excel")

class ConfiguracionMantencion(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='configuracion_mantencion')
    intervalo_horas = models.PositiveIntegerField(default=200, help_text="Horas para mantención preventiva")
    intervalo_km = models.PositiveIntegerField(default=10000, help_text="Kilómetros para mantención preventiva")
    
    class Meta:
        verbose_name = 'Configuración de Mantención'
        verbose_name_plural = 'Configuraciones de Mantención'
        
    def __str__(self):
        return f"Configuración {self.empresa.nombre_fantasia}"

# 2. USUARIOS (Custom User)
class Usuario(AbstractUser):
    ROLES = (
        ('OWNER', 'Dueño'),
        ('CHIEF', 'Jefe de Patio'),
        ('OPERATOR', 'Operador'),
        ('DISPATCHER', 'Despachador (Portería)'),
        ('FUEL', 'Cargador Combustible'),
        ('MECHANIC', 'Mecánico / Taller'),
    )
    ESTADOS = (
        ('DISPONIBLE', 'Disponible'),
        ('LICENCIA', 'Licencia Médica'),
        ('VACACIONES', 'Vacaciones'),
        ('DESVINCULADO', 'Desvinculado'),
        ('OTRO', 'Otro / No Disponible'),
    )
    rut = models.CharField(max_length=15, unique=True)
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    rol = models.CharField(max_length=20, choices=ROLES)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='DISPONIBLE')
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True)
    debe_cambiar_password = models.BooleanField(default=False, help_text='Si True, el usuario será redirigido a cambiar su contraseña al iniciar sesión.')
    
    # Manager para Multi-Tenancy pero preservando lógica de Auto-Usuario
    objects = UsuarioManager()

    def __str__(self):
        if self.nombre_completo:
            return f"{self.nombre_completo} - {self.rut}"
        return self.rut

# 3. MAQUINARIA
class Maquinaria(models.Model):
    UNIDADES = (('HORAS', 'Horas'), ('KM', 'Kilómetros'))
    ESTADOS = (('DISPONIBLE', 'Disponible'), ('EN_RUTA', 'En Ruta'), ('TALLER', 'En Taller'), ('VENDIDA', 'Vendida'), ('DESUSO', 'En Desuso'))
    TIPOS_MAQUINA = (
        ('RETROEXCAVADORA', 'Retroexcavadora'),
        ('EXCAVADORA', 'Excavadora'),
        ('CARGADOR_FRONTAL', 'Cargador Frontal'),
        ('MOTONIVELADORA', 'Motoniveladora'),
        ('RODILLO', 'Rodillo Compactador'),
        ('MINICARGADOR', 'Minicargador'),
        ('HORQUILLA', 'Grúa Horquilla'),
        ('CAMIONETA', 'Camioneta'),
        ('AUTOMOVIL', 'Automóvil'),
        ('GRUA', 'Grúa Pluma'),
        ('CAMION', 'Camión'),
        ('OTRO', 'Otro'),
    )
    
    id_interno = models.CharField(max_length=50)
    patente = models.CharField(max_length=20)
    tipo = models.CharField(max_length=50, choices=TIPOS_MAQUINA, default='OTRO')
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    tonelaje = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_combustible = models.CharField(max_length=20) # Diesel, Bencina, etc.
    unidad_medida = models.CharField(max_length=10, choices=UNIDADES)
    valor_actual_medida = models.DecimalField(max_digits=15, decimal_places=2)
    consumo_teorico = models.DecimalField(max_digits=10, decimal_places=2)
    proximo_mantenimiento = models.DecimalField(max_digits=15, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='DISPONIBLE')
    operador_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='maquinas_asignadas')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = EmpresaManager()

    def __str__(self):
        return f"Maq {self.id_interno} - Pat {self.patente}"

# 4. CHECKLIST
class Checklist(models.Model):
    maquina = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    niveles_ok = models.BooleanField(default=True)
    luces_ok = models.BooleanField(default=True)
    estructura_ok = models.BooleanField(default=True)
    comentarios = models.TextField(blank=True)
    firma_operador = models.TextField(blank=True, null=True, help_text="Firma digital guardada en Base64")
    fecha_revision = models.DateTimeField(auto_now_add=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = EmpresaManager()

# 5. ORDENES DE TRABAJO
class OrdenTrabajo(models.Model):
    maquina = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    operador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ordenes_operador')
    despachador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='ordenes_despacho')
    fecha_salida = models.DateTimeField(auto_now_add=True)
    fecha_entrada = models.DateTimeField(null=True, blank=True)
    medida_salida = models.DecimalField(max_digits=15, decimal_places=2)
    medida_entrada = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    correlativo = models.PositiveIntegerField(null=True, blank=True, help_text="Número correlativo interno por empresa")
    nro_guia_despacho = models.CharField(max_length=50, blank=True, null=True, help_text="Número de documento manual (Opcional)")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = EmpresaManager()

    def __str__(self):
        correlativo_str = f"OT-{self.correlativo:04d}" if self.correlativo else f"OT #{self.id}"
        return f"{correlativo_str} | Maq: {self.maquina.id_interno}"

    def clean(self):
        super().clean()
        # Validación de reglas de negocio SOLO para creación o salida de ruta (No para retornos)
        # Solo ejecutamos si tenemos una máquina asignada, para evitar RelatedObjectDoesNotExist en forms vacíos
        if not self.pk and hasattr(self, 'maquina_id') and self.maquina_id:
            hace_12_horas = timezone.now() - timedelta(hours=12)
            ultimo_checklist = Checklist.objects.filter(
                maquina=self.maquina,
                fecha_revision__gte=hace_12_horas
            ).order_by('-fecha_revision').first()

            if not ultimo_checklist:
                raise ValidationError("No se puede abrir una Orden de Trabajo: La máquina no tiene un Checklist registrado en las últimas 12 horas.")
            
            if not (ultimo_checklist.niveles_ok and ultimo_checklist.luces_ok and ultimo_checklist.estructura_ok):
                raise ValidationError("No se puede abrir una Orden de Trabajo: El último Checklist reporta fallas críticas.")

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk and not self.correlativo:
            # Autogenerar correlativo interno por empresa (Ej: 1, 2, 3...)
            ultimo = OrdenTrabajo._default_manager.filter(empresa=self.empresa).order_by('-correlativo').first()
            self.correlativo = (ultimo.correlativo + 1) if ultimo and ultimo.correlativo else 1
        super().save(*args, **kwargs)

# 6. GPS LOGS
class GPSLog(models.Model):
    maquina = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    latitud = models.DecimalField(max_digits=12, decimal_places=9)
    longitud = models.DecimalField(max_digits=12, decimal_places=9)
    velocidad = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = EmpresaManager()

# 7. COMBUSTIBLE LOGS (Consumo)
class CombustibleLog(models.Model):
    TIPOS = (('INTERNA', 'Carga Interna'), ('EXTERNA', 'Estación Servicio'))
    maquina = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    operador = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo_carga = models.CharField(max_length=20, choices=TIPOS)
    litros = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=15, decimal_places=2)
    medida_al_cargar = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_carga = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.SET_NULL, null=True, blank=True, help_text="OT opcional al momento de cargar")
    tipo_documento = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: Factura, Boleta, Guía (o en blanco si es interna)")
    numero_documento = models.CharField(max_length=50, blank=True, null=True)
    sello_flujometro = models.BigIntegerField(null=True, blank=True, help_text="Número de sello del flujómetro (Cargas internas)")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = EmpresaManager()

# 8. COMPRAS COMBUSTIBLE (Entradas)
class CompraCombustible(models.Model):
    fecha_compra = models.DateTimeField()
    nro_factura = models.CharField(max_length=50)
    cantidad_litros = models.DecimalField(max_digits=12, decimal_places=2)
    precio_litro = models.DecimalField(max_digits=10, decimal_places=2)
    total_pago = models.DecimalField(max_digits=15, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = EmpresaManager()

# 9. INVENTARIO COMBUSTIBLE (Saldo Actual)
class InventarioCombustible(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE)
    stock_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    precio_promedio_ponderado = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    objects = EmpresaManager()

# 10. TALLER / MANTENIMIENTO
class OrdenTaller(models.Model):
    TIPOS_MANTENIMIENTO = (
        ('PREVENTIVO', 'Preventivo (Por Horómetro/Km)'),
        ('CORRECTIVO', 'Correctivo (Por Falla/Rotura)'),
        ('RUTINARIO', 'Revisión Diaria / Rutinaria'),
    )
    ESTADOS_TALLER = (
        ('EN_PROCESO', 'En Proceso'),
        ('ESPERANDO_REPUESTO', 'Esperando Repuesto'),
        ('FINALIZADO', 'Finalizado'),
    )
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    maquina = models.ForeignKey(Maquinaria, on_delete=models.CASCADE, related_name='ordenes_taller')
    mecanico = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, limit_choices_to={'rol__in': ['MECHANIC', 'CHIEF', 'OWNER']})
    
    tipo_mantenimiento = models.CharField(max_length=20, choices=TIPOS_MANTENIMIENTO)
    estado = models.CharField(max_length=20, choices=ESTADOS_TALLER, default='EN_PROCESO')
    
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    
    medida_ingreso = models.DecimalField(max_digits=10, decimal_places=2, help_text="Horómetro o KM al entrar al taller")
    medida_salida = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    descripcion_falla = models.TextField(help_text="Motivo de ingreso o falla reportada")
    trabajo_realizado = models.TextField(null=True, blank=True, help_text="Detalle de las reparaciones efectuadas")
    
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Suma de mano de obra y repuestos")
    
    objects = EmpresaManager()

    def __str__(self):
        return f"OT Taller #{self.id} - {self.maquina.id_interno} - {self.get_estado_display()}"