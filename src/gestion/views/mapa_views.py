from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import Maquinaria, GPSLog
from ..utils import modulo_requerido
import logging

logger = logging.getLogger('gestion')

@login_required(login_url='web_login')
@modulo_requerido('modulo_gps')
def mapa_en_vivo(request):
    """
    Renderiza la plantilla base del mapa (Leaflet.js)
    """
    return render(request, 'gestion/mapa/mapa_live.html')

@login_required
def api_posiciones(request):
    """
    Endpoint JSON para el consumo del Mapa.
    Devuelve la última coordenada conocida de CADA máquina de la empresa.
    """
    try:
        maquinas = Maquinaria.objects.filter(empresa=request.empresa)
        data = []
        
        for m in maquinas:
            # Traer el último log para esta máquina (ordenado por id descendente o timestamp)
            ultimo_log = GPSLog.objects.filter(maquina=m).order_by('-timestamp').first()
            
            if ultimo_log:
                # Determinar si está moviéndose (velocidad > 0)
                isActive = float(ultimo_log.velocidad) > 2.0  # Si va a más de 2 km/h consideramos activa
                
                data.append({
                    'id_maquina': m.id_interno,
                    'patente': m.patente,
                    'lat': float(ultimo_log.latitud),
                    'lng': float(ultimo_log.longitud),
                    'velocidad': float(ultimo_log.velocidad),
                    'is_active': isActive,
                    'fecha_hora': ultimo_log.timestamp.strftime('%d-%m-%Y %H:%M:%S'),
                    'estado': m.get_estado_display()
                })

        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        logger.error(f"Error cargando API posiciones GPS: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
