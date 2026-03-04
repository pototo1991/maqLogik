from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Maquinaria, OrdenTrabajo, Checklist, OrdenTaller, CombustibleLog
from ..utils import render_to_pdf, modulo_requerido

@login_required(login_url='web_login')
@modulo_requerido('modulo_reporteria')
def reportes_dashboard(request):
    """
    Vista principal del Panel de Reportes. 
    Muestra los filtros y botones de descarga PDF para cada tipo de informe.
    """
    # Extraemos máquinas para los filtros de Historial Clínico
    maquinas = Maquinaria.objects.filter(empresa=request.empresa).order_by('id_interno')
    
    # Fecha por defecto para inputs
    hoy = timezone.now().date()
    # Generar inicio de mes por defecto
    inicio_mes = hoy.replace(day=1)
    
    context = {
        'maquinas': maquinas,
        'fecha_hoy': hoy.strftime('%Y-%m-%d'),
        'fecha_inicio_mes': inicio_mes.strftime('%Y-%m-%d')
    }
    return render(request, 'gestion/reportes/dashboard.html', context)

@login_required(login_url='web_login')
def generar_pdf(request, tipo_reporte):
    """
    Controlador maestro (Router) para las descargas de PDF.
    Intercepta el 'tipo_reporte' y deriva a la sub-función lógica pertinente.
    """
    if tipo_reporte == 'actividad_terreno':
        return _pdf_actividad_terreno(request)
        
    elif tipo_reporte == 'historial_clinico':
        return _pdf_historial_clinico(request)
        
    elif tipo_reporte == 'rendimiento_combustible':
        return _pdf_rendimiento_combustible(request)
        
    else:
        # Retorno seguro si el tipo no es mapeable
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Tipo de reporte desconocido'})

# =========================================================
# Lógica Privada de Generación de Cada PDF
# =========================================================

def _pdf_actividad_terreno(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Debe especificar un rango de fechas para este reporte.'})
        
    # Limites para incluir todo el día en endDate
    try:
        from datetime import datetime, time
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Formato de fecha inválido.'})
        
    # O.T. finalizadas (fecha_entrada registrada = retornaron) dentro del rango
    # Una OT se considera cerrada cuando tiene fecha_entrada (retorno de terreno)
    ordenes = OrdenTrabajo.objects.filter(
        empresa=request.empresa,
        fecha_entrada__isnull=False,
        fecha_salida__range=[start_date, end_date]
    ).order_by('-fecha_entrada')
    
    # Checklists completados en el rango
    checklists = Checklist.objects.filter(
        empresa=request.empresa,
        fecha_revision__range=[start_date, end_date]
    ).order_by('fecha_revision')
    
    context = {
        'empresa': request.empresa,
        'usuario': request.user,
        'fecha_inicio': start_date.strftime('%d/%m/%Y'),
        'fecha_fin': end_date.strftime('%d/%m/%Y'),
        'fecha_generacion': timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M'),
        'ordenes': ordenes,
        'checklists': checklists,
    }
    
    # Renderizamos la plantilla Hacia el Motor de xhtml2pdf
    pdf = render_to_pdf('gestion/reportes/actividad_terreno_pdf.html', context)
    
    if pdf:
        # Configurar nombre del archivo de descarga
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Reporte_Terreno_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.pdf"
        # Si se quiere que se muestre en el browser primero en vez de descargar, se usa 'inline'
        content = f"inline; filename={filename}"
        response['Content-Disposition'] = content
        return response
        
    return render(request, 'gestion/reportes/dashboard.html', {'error': 'Error de renderizado al generar el documento PDF.'})

def _pdf_historial_clinico(request):
    maquina_id = request.GET.get('maquina_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not maquina_id:
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Debe seleccionar una máquina para generar su historial.'})
        
    try:
        from datetime import datetime
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except Exception:
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Formato de fecha inválido.'})
        
    # Obtener el objeto Máquina
    from django.shortcuts import get_object_or_404
    maquina = get_object_or_404(Maquinaria, pk=maquina_id, empresa=request.empresa)
    
    # Filtrar solo las O.T. de Taller finalizadas de esta máquina
    historial = OrdenTaller.objects.filter(
        empresa=request.empresa,
        maquina=maquina,
        estado='FINALIZADO',
        fecha_salida__range=[start_date, end_date]
    ).order_by('-fecha_salida')
    
    context = {
        'empresa': request.empresa,
        'usuario': request.user,
        'maquina': maquina,
        'fecha_inicio': start_date.strftime('%d/%m/%Y'),
        'fecha_fin': end_date.strftime('%d/%m/%Y'),
        'fecha_generacion': timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M'),
        'historial': historial,
    }
    
    pdf = render_to_pdf('gestion/reportes/historial_clinico_pdf.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Historial_Taller_{maquina.id_interno}.pdf"
        response['Content-Disposition'] = f"inline; filename={filename}"
        return response
        
    return render(request, 'gestion/reportes/dashboard.html', {'error': 'Error al generar el Historial PDF.'})

from django.db.models import Sum

def _pdf_rendimiento_combustible(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Debe especificar un rango de fechas.'})
        
    try:
        from datetime import datetime
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except Exception:
        return render(request, 'gestion/reportes/dashboard.html', {'error': 'Formato de fecha inválido.'})
        
    # Obtener todas las recargas en el rango
    recargas = CombustibleLog.objects.filter(
        empresa=request.empresa,
        fecha_carga__range=[start_date, end_date]
    ).select_related('maquina', 'operador').order_by('fecha_carga')
    
    # Consolidado general para métricas clave
    total_litros = recargas.aggregate(Sum('litros'))['litros__sum'] or 0
    total_costo = recargas.aggregate(Sum('costo_total'))['costo_total__sum'] or 0
    
    # Análisis por Máquina
    from django.db.models import Count
    resumen_maquinas = CombustibleLog.objects.filter(
        empresa=request.empresa,
        fecha_carga__range=[start_date, end_date]
    ).values(
        'maquina__id_interno', 'maquina__tipo'
    ).annotate(
        total_litros=Sum('litros'),
        total_costo=Sum('costo_total'),
        numero_cargas=Count('id')
    ).order_by('-total_litros')
    
    context = {
        'empresa': request.empresa,
        'usuario': request.user,
        'fecha_inicio': start_date.strftime('%d/%m/%Y'),
        'fecha_fin': end_date.strftime('%d/%m/%Y'),
        'fecha_generacion': timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M'),
        'recargas': recargas,
        'total_litros': total_litros,
        'total_costo': total_costo,
        'resumen_maquinas': resumen_maquinas,
    }
    
    pdf = render_to_pdf('gestion/reportes/rendimiento_combustible_pdf.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Control_Combustible_{start_date.strftime('%Y%m')}.pdf"
        response['Content-Disposition'] = f"inline; filename={filename}"
        return response
        
    return render(request, 'gestion/reportes/dashboard.html', {'error': 'Error al generar el PDF de Rendimiento.'})
