from rest_framework import serializers
from .models import (
    Usuario, Maquinaria, Checklist,
    GPSLog, OrdenTrabajo, CombustibleLog, OrdenTaller
)


# ─────────────────────────────────────────────────
#  PERFIL DE USUARIO (endpoint /api/v1/me/)
# ─────────────────────────────────────────────────
class UsuarioSerializer(serializers.ModelSerializer):
    """
    Solo lectura. Devuelve el perfil del usuario autenticado por JWT.
    Nunca expone la contraseña ni campos sensibles.
    """
    empresa_nombre = serializers.CharField(source='empresa.nombre_fantasia', read_only=True)
    rol_display    = serializers.CharField(source='get_rol_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model  = Usuario
        fields = [
            'id', 'username', 'nombre_completo', 'rut',
            'telefono', 'rol', 'rol_display',
            'estado', 'estado_display',
            'empresa_nombre', 'is_superuser',
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────
#  MAQUINARIA
# ─────────────────────────────────────────────────
class MaquinariaSerializer(serializers.ModelSerializer):
    tipo_display   = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    operador_nombre = serializers.CharField(
        source='operador_asignado.nombre_completo', read_only=True
    )

    class Meta:
        model   = Maquinaria
        # empresa se inyecta desde el ViewSet, nunca desde el cliente
        exclude = ['empresa']


# ─────────────────────────────────────────────────
#  CHECKLIST
# ─────────────────────────────────────────────────
class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model   = Checklist
        # empresa y usuario se inyectan desde el ViewSet
        exclude = ['empresa', 'usuario']


# ─────────────────────────────────────────────────
#  GPS LOG
# ─────────────────────────────────────────────────
class GPSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model   = GPSLog
        exclude = ['empresa']


# ─────────────────────────────────────────────────
#  ÓRDENES DE TRABAJO
# ─────────────────────────────────────────────────
class OrdenTrabajoSerializer(serializers.ModelSerializer):
    """
    - Creación (POST): El campo empresa y operador se inyectan automáticamente.
    - Cierre (PATCH): Solo se permiten actualizar medida_entrada y fecha_entrada.
    """
    maquina_patente   = serializers.CharField(source='maquina.patente', read_only=True)
    operador_nombre   = serializers.CharField(source='operador.nombre_completo', read_only=True)
    duracion_horas    = serializers.SerializerMethodField()

    class Meta:
        model   = OrdenTrabajo
        exclude = ['empresa']
        read_only_fields = ['operador', 'fecha_salida']

    def get_duracion_horas(self, obj) -> float | None:
        if obj.fecha_entrada and obj.fecha_salida:
            delta = obj.fecha_entrada - obj.fecha_salida
            return round(delta.total_seconds() / 3600, 2)
        return None


# ─────────────────────────────────────────────────
#  COMBUSTIBLE LOG
# ─────────────────────────────────────────────────
class CombustibleLogSerializer(serializers.ModelSerializer):
    """
    Registro de carga de combustible.
    empresa y operador se inyectan desde el ViewSet (no los envía el móvil).
    """
    tipo_carga_display = serializers.CharField(source='get_tipo_carga_display', read_only=True)

    class Meta:
        model   = CombustibleLog
        exclude = ['empresa', 'operador']

    def validate(self, data):
        """ Validación: el costo_total debe coincidir con litros × precio_unitario """
        litros  = data.get('litros', 0)
        precio  = data.get('precio_unitario', 0)
        costo   = data.get('costo_total', 0)
        esperado = round(litros * precio, 2)
        if abs(float(costo) - esperado) > 1:  # tolerancia de $1
            raise serializers.ValidationError(
                f"costo_total ({costo}) no coincide con litros × precio ({esperado})."
            )
        return data


# ─────────────────────────────────────────────────
#  ORDEN DE TALLER
# ─────────────────────────────────────────────────
class OrdenTallerSerializer(serializers.ModelSerializer):
    """
    Órdenes de mantenimiento / reparación.
    empresa se inyecta desde el ViewSet.
    """
    tipo_mantenimiento_display = serializers.CharField(
        source='get_tipo_mantenimiento_display', read_only=True
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    maquina_patente = serializers.CharField(source='maquina.patente', read_only=True)
    mecanico_nombre = serializers.CharField(source='mecanico.nombre_completo', read_only=True)

    class Meta:
        model   = OrdenTaller
        exclude = ['empresa']
