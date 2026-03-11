from django.http import HttpResponseRedirect
from django.urls import reverse
import threading

_thread_local = threading.local()

def get_current_empresa():
    return getattr(_thread_local, 'empresa', None)

class EmpresaMiddleware:
    """
    Middleware para capturar la empresa del usuario actual en cada request
    y guardarla en un thread-local, permitiendo acceder a ella desde cualquier
    lugar del código (ej. Model Managers) garantizando aislación SaaS.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        empresa_asignada = None
        
        # 1. ¿Está el superadmin simulando ser (impersonate) un cliente?
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            impersonate_id = None
            
            # A) Si es API (Móvil), leemos el Header
            if request.path.startswith('/api/'):
                impersonate_id = request.headers.get('X-Empresa-Id')
            # B) Si es Web, leemos la sesión
            elif hasattr(request, 'session'):
                impersonate_id = request.session.get('impersonate_empresa_id')

            if impersonate_id:
                from .models import Empresa
                empresa_asignada = Empresa.objects.filter(id=impersonate_id).first()
                if not empresa_asignada and hasattr(request, 'session') and 'impersonate_empresa_id' in request.session:
                    del request.session['impersonate_empresa_id'] # Limpiar si no existe
        
        # 2. Flujo normal: Si no hay impersonate, intentar obtener la empresa del perfil
        if not empresa_asignada and request.user.is_authenticated and hasattr(request.user, 'empresa'):
            empresa_asignada = request.user.empresa
            
        # 3. Asignación global a Request y ThreadLocal    
        if empresa_asignada:
            _thread_local.empresa = empresa_asignada
            request.empresa = empresa_asignada
        else:
            _thread_local.empresa = None
            request.empresa = None
            
        # 4. PROTECCIÓN SAAS: 
        # Si un superusuario entra a la web (no API) y está intentando acceder a una vista "de cliente"
        # (checklists, ordenes, dashboard de cliente) SIN estar impersonando a una empresa, 
        # lo devolvemos obligatoriamente al panel maestro (Root SaaS).
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            ruta = request.path
            es_ruta_api = ruta.startswith('/api/')
            es_ruta_root = ruta.startswith('/root/')
            es_ruta_auth = ruta in ['/login/', '/logout/', '/'] or ruta.startswith('/admin/')
            
            # Si no está en su panel maestro, ni en auth, ni en la API móvil y no tiene empresa
            if not es_ruta_api and not es_ruta_root and not es_ruta_auth and request.empresa is None:
                # Redirigir al panel de administración de inquilinos
                return HttpResponseRedirect(reverse('root_dashboard'))
            
        response = self.get_response(request)
        
        # Limpieza después del request para evitar fugas entre hilos
        _thread_local.empresa = None
        
        return response


class NoCacheMiddleware:
    """
    Middleware que inyecta headers anti-cache a TODAS las respuestas del usuario
    logueado, previniendo que el navegador guarde una foto de las páginas en
    su historial local (BFCache). Así, el botón 'Atrás' no puede mostrar
    datos de una sesión ya cerrada.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Inyectar anti-cache si: está autenticado, o es la página de login, o es 403 (Acceso Denegado)
        path = request.path
        if (hasattr(request, 'user') and request.user.is_authenticated) or \
           path in ['/', '/login/'] or \
           response.status_code == 403:
            
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response
