from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import logging

logger = logging.getLogger('gestion')

def web_login(request):
    """
    Vista Web para inicio de sesión en el Dashboard.
    Usa sesiones tradicionales en lugar de JWT (El cual es solo para API Móvil).
    """
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('root_dashboard')
        return redirect('dashboard')
        
    if request.method == 'POST':
        rut_usuario = request.POST.get('username')
        clave = request.POST.get('password')
        
        user = authenticate(request, username=rut_usuario, password=clave)
        if user is not None:
            # Validación de Módulos vs Rol del Usuario
            if not user.is_superuser and user.empresa:
                if user.rol == 'MECHANIC' and not user.empresa.modulo_mantencion:
                    logger.warning(f"AUDITORÍA - Login bloqueado: Usuario '{user.username}' intentó entrar como Mecánico, pero la empresa {user.empresa.nombre_fantasia} tiene el módulo Taller apagado.")
                    messages.error(request, 'Acceso Denegado: Su empresa no tiene contratado o ha desactivado el Módulo de Taller Mecánico.')
                    return render(request, 'gestion/auth/login.html')
                
                if user.rol == 'FUEL' and not user.empresa.modulo_combustible:
                    logger.warning(f"AUDITORÍA - Login bloqueado: Usuario '{user.username}' intentó entrar como Cargador, pero la empresa {user.empresa.nombre_fantasia} tiene el módulo Combustible apagado.")
                    messages.error(request, 'Acceso Denegado: Su empresa no tiene contratado o ha desactivado el Módulo de Combustible.')
                    return render(request, 'gestion/auth/login.html')

            login(request, user)
            logger.info(f"AUDITORÍA - Login Web Exitoso: Usuario '{user.username}' ({user.get_rol_display()}) de la empresa '{user.empresa.nombre_fantasia if user.empresa else 'System Admin'}'.")
            
            # Redirección inteligente basada en rol
            if user.is_superuser:
                return redirect('root_dashboard')
            else:
                return redirect('dashboard')
        else:
            logger.warning(f"AUDITORÍA - Intento fallido de Login Web: Credenciales inválidas para el rut: '{rut_usuario}'. IP: {request.META.get('REMOTE_ADDR')}")
            messages.error(request, 'Usuario o contraseña incorrectos.')
            
    return render(request, 'gestion/auth/login.html')

def web_logout(request):
    if request.user.is_authenticated:
        logger.info(f"AUDITORÍA - Logout Web: Usuario '{request.user.username}' cerró sesión.")
    logout(request)
    
    # Destruir proactivamente la sesión y la cookie de la memoria
    request.session.flush()
    response = redirect('web_login')
    response.delete_cookie('sessionid')
    return response


from django.contrib.auth.decorators import login_required
from ..forms import PerfilForm

@login_required
def mi_perfil(request):
    """
    Vista para que el usuario vea y edite sus datos personales básicos.
    Campos editables: nombres, apellido, email, teléfono.
    Campos de solo lectura: rol, estado, RUT, empresa.
    """
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Tu perfil ha sido actualizado correctamente.')
            logger.info(f"AUDITORÍA - Perfil actualizado: Usuario '{request.user.username}' actualizó sus datos personales.")
            return redirect('mi_perfil')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'gestion/auth/mi_perfil.html', {'form': form})

