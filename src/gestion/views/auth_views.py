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
        return redirect('dashboard') # Redirigir si ya está logueado
        
    if request.method == 'POST':
        rut_usuario = request.POST.get('username')
        clave = request.POST.get('password')
        
        user = authenticate(request, username=rut_usuario, password=clave)
        if user is not None:
            login(request, user)
            logger.info(f"AUDITORÍA - Login Web Exitoso: Usuario '{user.username}' ({user.get_rol_display()}) de la empresa '{user.empresa.nombre_fantasia if user.empresa else 'System Admin'}'.")
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
