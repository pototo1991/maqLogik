from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Empresa, Usuario, Maquinaria, Checklist, OrdenTrabajo, GPSLog, CombustibleLog, CompraCombustible, InventarioCombustible

# 1. EMPRESAS
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre_fantasia', 'rut_empresa', 'usa_despachador')
    search_fields = ('nombre_fantasia', 'rut_empresa')

# 2. USUARIOS (Custom UserAdmin)
@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'nombre_completo', 'rol', 'empresa', 'is_staff')
    list_filter = ('rol', 'empresa', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Datos MaqLogik', {'fields': ('rut', 'nombre_completo', 'telefono', 'rol', 'valor_hora', 'empresa')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos MaqLogik', {'fields': ('rut', 'nombre_completo', 'telefono', 'rol', 'valor_hora', 'empresa')}),
    )
    search_fields = ('username', 'nombre_completo', 'rut')

# 3. MAQUINARIA
@admin.register(Maquinaria)
class MaquinariaAdmin(admin.ModelAdmin):
    list_display = ('id_interno', 'patente', 'marca', 'modelo', 'estado', 'empresa')
    list_filter = ('estado', 'empresa', 'tipo_combustible')
    search_fields = ('id_interno', 'patente', 'marca')

# 4. CHECKLIST
@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'usuario', 'fecha_revision', 'niveles_ok', 'luces_ok', 'estructura_ok', 'empresa')
    list_filter = ('empresa', 'niveles_ok', 'luces_ok', 'estructura_ok')
    date_hierarchy = 'fecha_revision'

# 5. ORDENES DE TRABAJO
@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'operador', 'fecha_salida', 'fecha_entrada', 'nro_guia_despacho', 'empresa')
    list_filter = ('empresa', 'maquina')
    date_hierarchy = 'fecha_salida'

# 6. GPS LOGS
@admin.register(GPSLog)
class GPSLogAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'latitud', 'longitud', 'velocidad', 'timestamp', 'empresa')
    list_filter = ('empresa', 'maquina')
    date_hierarchy = 'timestamp'

# 7. COMBUSTIBLE LOGS (Consumo)
@admin.register(CombustibleLog)
class CombustibleLogAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'operador', 'tipo_carga', 'litros', 'costo_total', 'empresa')
    list_filter = ('tipo_carga', 'empresa', 'maquina')

# 8. COMPRAS COMBUSTIBLE (Entradas)
@admin.register(CompraCombustible)
class CompraCombustibleAdmin(admin.ModelAdmin):
    list_display = ('fecha_compra', 'nro_factura', 'cantidad_litros', 'total_pago', 'empresa')
    list_filter = ('empresa',)
    date_hierarchy = 'fecha_compra'

# 9. INVENTARIO COMBUSTIBLE (Saldo Actual)
@admin.register(InventarioCombustible)
class InventarioCombustibleAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'stock_actual', 'precio_promedio_ponderado')
    list_filter = ('empresa',)
