from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from ..models import Empresa
import logging

logger = logging.getLogger('gestion')

def is_superadmin(user):
    """ Verifica que el usuario tenga privilegios de Root SaaS """
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superadmin, login_url='/')
def root_dashboard(request):
    """ Panel de Control Maestro para Administración de MaqLogik SaaS """
    empresas = Empresa.objects.all().order_by('-id')
    
    # KPIs Rápidos
    total_empresas = empresas.count()
    
    # Data para Gráficos
    empresas_activas = empresas.filter(activa=True).count()
    empresas_inactivas = empresas.filter(activa=False).count()
    
    modulos_data = [
        empresas.filter(modulo_gps=True).count(),
        empresas.filter(modulo_mantencion=True).count(),
        empresas.filter(modulo_combustible=True).count(),
        empresas.filter(modulo_checklist=True).count(),
        empresas.filter(modulo_reporteria=True).count()
    ]
    
    context = {
        'empresas': empresas,
        'total_empresas': total_empresas,
        'empresas_activas': empresas_activas,
        'empresas_inactivas': empresas_inactivas,
        'modulos_data': modulos_data,
    }
    return render(request, 'gestion/root/dashboard.html', context)

from django.db import transaction
from ..forms import EmpresaForm, UsuarioCreationForm, ConfiguracionMantencionForm
from ..models import Usuario, ConfiguracionMantencion

@user_passes_test(is_superadmin, login_url='/')
def root_create_empresa(request):
    """ Vista para crear una Nueva Empresa con sus respectivos módulos """
    if request.method == 'POST':
        form_empresa = EmpresaForm(request.POST)
        form_owner = UsuarioCreationForm(request.POST)
        form_mantencion = ConfiguracionMantencionForm(request.POST)
        
        if form_empresa.is_valid() and form_owner.is_valid() and form_mantencion.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear Empresa
                    nueva_empresa = form_empresa.save()
                    
                    # 1.5 Crear Configuracion Mantencion
                    nueva_config = form_mantencion.save(commit=False)
                    nueva_config.empresa = nueva_empresa
                    nueva_config.save()
                    
                    # 2. Asignarle el formulario de Owner a esa empresa
                    nuevo_owner = form_owner.save(commit=False)
                    nuevo_owner.empresa = nueva_empresa
                    nuevo_owner.rol = 'OWNER'
                    nuevo_owner.save()
                    
                logger.info(f"AUDITORÍA - Nueva Empresa SaaS Creada: '{nueva_empresa.nombre_fantasia}' (RUT: {nueva_empresa.rut_empresa}) por el administrador {request.user.username}.")
                messages.success(request, f"¡Empresa {nueva_empresa.nombre_fantasia} creada con éxito y Owner asignado!")
                return redirect('root_dashboard')
            except Exception as e:
                logger.error(f"AUDITORÍA - EXCEPCIÓN DB AL CREAR EMPRESA: {str(e)}")
                messages.error(request, f"Error interno al crear Empresa/Owner: {str(e)}")
        else:
            errors_msg = "Revise: "
            if form_empresa.errors:
                errors_msg += f"Empresa: {form_empresa.errors.as_text()} | "
            if form_owner.errors:
                errors_msg += f"Owner: {form_owner.errors.as_text()} | "
            if form_mantencion.errors:
                errors_msg += f"Mantención: {form_mantencion.errors.as_text()}"
            
            # Formateando y enviando los errores exactos a los logs del archivo app_control.log
            logger.warning(f"AUDITORÍA - Falla de validación de Formulario al crear empresa: {errors_msg.replace('  ', ' ')}")
            messages.error(request, errors_msg)
    else:
        form_empresa = EmpresaForm()
        form_owner = UsuarioCreationForm()
        form_mantencion = ConfiguracionMantencionForm()

        
    context = {
        'form_empresa': form_empresa,
        'form_owner': form_owner,
        'form_mantencion': form_mantencion
    }
    return render(request, 'gestion/root/nueva_empresa.html', context)

@user_passes_test(is_superadmin, login_url='/')
def root_edit_modules(request, empresa_id):
    """ Vista para editar los módulos contratados de una Empresa (SaaS Features) """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    config_mantencion, created = ConfiguracionMantencion.objects.get_or_create(empresa=empresa)
    
    if request.method == 'POST':
        # Le pasamos la instancia existente para que haga Update en lugar de Create
        form = EmpresaForm(request.POST, instance=empresa)
        form_mantencion = ConfiguracionMantencionForm(request.POST, instance=config_mantencion)
        if form.is_valid() and form_mantencion.is_valid():
            form.save()
            form_mantencion.save()
            messages.success(request, f"¡Módulos de la empresa {empresa.nombre_fantasia} actualizados correctamente!")
            return redirect('root_dashboard')
        else:
            messages.error(request, "Error al actualizar los módulos. Verifique los campos.")
    else:
        form = EmpresaForm(instance=empresa)
        form_mantencion = ConfiguracionMantencionForm(instance=config_mantencion)
        
    context = {
        'form': form,
        'form_mantencion': form_mantencion,
        'empresa': empresa
    }
    return render(request, 'gestion/root/editar_modulos.html', context)

from django.contrib.auth.forms import SetPasswordForm

@user_passes_test(is_superadmin, login_url='/')
def root_manage_owner(request, empresa_id):
    """ Vista para gestionar credenciales y password del Owner local de la Empresa """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    # IMPORTANTE: Usamos la relación inversa (empresa.usuario_set) en lugar de Usuario.objects
    # porque el UsuarioManager custom filtra por empresa en sesión y el Superadmin no tiene empresa.
    owner = empresa.usuario_set.filter(rol='OWNER').first()
    
    if not owner:
        messages.error(request, f"La empresa {empresa.nombre_fantasia} aún no tiene un Owner asignado.")
        return redirect('root_dashboard')
        
    if request.method == 'POST':
        # Instanciamos SetPasswordForm (requerido para resetar password ignorando la antigua por parte un admin)
        form = SetPasswordForm(user=owner, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contraseña del Owner '{owner.username}' actualizada exitosamente.")
            return redirect('root_dashboard')
        else:
            messages.error(request, "Vuelva a verificar que las contraseñas coinciden.")
    else:
        # Pasa el usuario Owner
        form = SetPasswordForm(user=owner)
        
    context = {
        'form': form,
        'empresa': empresa,
        'owner': owner
    }
    return render(request, 'gestion/root/gestionar_owner.html', context)

@user_passes_test(is_superadmin, login_url='/')
def root_impersonate(request, empresa_id):
    """ 
    Permite al Superusuario 'Ver como' si fuera un empleado de esta Empresa.
    Guarda el ID temporalmente en la sesión, el cual debe ser leído por el Middleware.
    """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    request.session['impersonate_empresa_id'] = empresa.id
    messages.info(request, f"👀 Estás viendo el sistema como: {empresa.nombre_fantasia}")
    return redirect('dashboard')  # Enviamos al dashboard principal de la app

@user_passes_test(is_superadmin, login_url='/')
def root_stop_impersonate(request):
    """ Sale del modo 'Ver como' y destruye la variable de sesión """
    if 'impersonate_empresa_id' in request.session:
        del request.session['impersonate_empresa_id']
        messages.success(request, "Has regresado al Panel de Control Maestro (SaaS).")
    return redirect('root_dashboard')

@user_passes_test(is_superadmin, login_url='/')
def root_toggle_empresa_status(request, empresa_id):
    """ 
    Invierte el estado de 'activa' de una empresa (Soft Delete/Restore).
    También desactiva masivamente todos los usuarios asociados para denegar logins,
    excluyendo expresamente a los superusuarios.
    """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    usuarios_empresa = Usuario.objects.filter(empresa=empresa)
    
    # Toggle del booleano
    nuevo_estado = not empresa.activa
    empresa.activa = nuevo_estado
    empresa.save()

    # Actualizar is_active forzosamente a todos los empleados conectados a la empresa
    # EXCEPTO al panel maestro / superusuarios para evitar bloqueos del sistema.
    usuarios_empresa.exclude(is_superuser=True).update(is_active=nuevo_estado)

    # Mensajes UI
    accion = "Habilitada" if nuevo_estado else "Deshabilitada (Soft Delete aplicado)"
    color = messages.success if nuevo_estado else messages.warning
    color(request, f"La empresa {empresa.nombre_fantasia} fue {accion}.")
    
    return redirect('root_dashboard')
