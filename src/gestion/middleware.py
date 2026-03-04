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
            impersonate_id = request.session.get('impersonate_empresa_id')
            if impersonate_id:
                from .models import Empresa
                empresa_asignada = Empresa.objects.filter(id=impersonate_id).first()
                if not empresa_asignada:
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
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response
