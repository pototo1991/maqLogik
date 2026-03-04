from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings

def link_callback(uri, rel):
    """
    Convierte las URIs HTML a rutas absolutas del sistema para que xhtml2pdf 
    pueda acceder a las imágenes y CSS de la carpeta STATIC_ROOT / MEDIA_ROOT.
    """
    # Usando el directorio local en Windows
    # static_url e.g. '/static/'
    sUrl = settings.STATIC_URL
    sRoot = settings.STATIC_ROOT

    # media_url e.g. '/media/'
    mUrl = settings.MEDIA_URL
    mRoot = settings.MEDIA_ROOT

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        # Si no hay STATIC_ROOT definido (desarrollo), intentamos buscar en la carpeta de app
        if sRoot:
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, 'src', 'gestion', 'static', uri.replace(sUrl, ""))
            path = path.replace('\\', '/')
    else:
        return uri

    # Asegurarse de que el archivo existe
    if not os.path.isfile(path):
            raise Exception(f'URI de medio {uri} no encontrada (Buscado en {path})')
            
    return path

def render_to_pdf(template_src, context_dict={}):
    """
    Toma una ruta de plantilla HTML y un diccionario de contexto Django,
    lo renderiza y lo escupe como un objeto HttpResponse binario PDF.
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    
    result = BytesIO()
    
    # Pasamos el html convertido a Bytes, al conversor Pisa de xhtml2pdf
    # link_callback se asegura de incrustar CSS e Imágenes locales
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import render

def modulo_requerido(nombre_modulo):
    """
    Decorador Multi-Tenant:
    Verifica si la Empresa del usuario actual tiene contratado (True) el módulo solicitado.
    Si no lo tiene, retorna una pantalla de 'Acceso Denegado / Upsell'.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Si es superusuario, lo dejamos pasar siempre por si está auditiando
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            # Verificar si existe request.empresa y leer el valor del campo booleano
            if hasattr(request, 'empresa') and request.empresa:
                tiene_modulo = getattr(request.empresa, nombre_modulo, False)
                if tiene_modulo:
                    return view_func(request, *args, **kwargs)
                    
            # Si llega aquí, es porque el módulo es False (o no tiene empresa)
            context = {
                'modulo_solicitado': nombre_modulo.replace('modulo_', '').replace('_', ' ').title()
            }
            # Por ahora devolveremos un simple Forbidden Text. 
            # Luego podemos crear un template html bonito de upsell ('gestion/upsell_denied.html')
            return HttpResponseForbidden(f"Acceso Denegado: Su empresa no ha contratado el módulo {context['modulo_solicitado']}. Contacte a Ventas de MaqLogik.")
        return _wrapped_view
    return decorator
