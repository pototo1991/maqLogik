import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Maquinaria, Usuario, Checklist, OrdenTrabajo

@login_required
def exportar_csv(request, tipo):
    """
    Controlador genérico para descargar datos en formato CSV (Compatible con Excel).
    Recibe un string 'tipo' que ruteará al queryset y cabeceras correctas.
    """
    response = HttpResponse(content_type='text/csv; charset=cp1252')
    response.charset = 'cp1252' # Windows Latin-1: Excel en español lo interpreta directamente sin distorsionar tildes o ñ
    
    # Nombre de archivo dinámico
    fecha_hoy = timezone.now().strftime('%Y%m%d_%H%M')
    response['Content-Disposition'] = f'attachment; filename="Listado_{tipo.capitalize()}_{fecha_hoy}.csv"'

    writer = csv.writer(response, delimiter=';') # Excel en español prefiere usar punto y coma
    
    # Ruteador de Entidades
    if tipo == 'maquinarias':
        writer.writerow(['ID Interno', 'Patente', 'Tipo', 'Marca', 'Modelo', 'Estado', 'Combustible', 'U. Medida', 'Valor Actual'])
        maquinas = Maquinaria.objects.filter(empresa=request.user.empresa).order_by('id_interno')
        for m in maquinas:
            writer.writerow([
                m.id_interno,
                m.patente or '-',
                m.tipo or '-',
                m.marca or '-',
                m.modelo or '-',
                m.get_estado_display(),
                m.tipo_combustible,
                m.get_unidad_medida_display(),
                m.valor_actual_medida
            ])

    elif tipo == 'usuarios':
        writer.writerow(['Usuario', 'Nombre Completo', 'RUT', 'Email', 'Teléfono', 'Rol', 'Valor Hora', 'Activo'])
        usuarios = Usuario.objects.filter(empresa=request.empresa).order_by('username')
        for u in usuarios:
            writer.writerow([
                u.username,
                u.nombre_completo or u.get_full_name() or '-',
                u.rut or '-',
                u.email or '-',
                u.telefono or '-',
                u.get_rol_display(),
                u.valor_hora,
                'Sí' if u.is_active else 'No'
            ])

    elif tipo == 'checklists':
        writer.writerow(['Fecha y Hora', 'Máquina', 'Operador', 'Estado General', 'Comentarios'])
        checklists = Checklist.objects.filter(empresa=request.empresa).select_related('maquina', 'usuario').order_by('-fecha_revision')
        for c in checklists:
            estado_gen = "OK" if c.niveles_ok and c.luces_ok and c.estructura_ok else "CON FALLAS"
            writer.writerow([
                timezone.localtime(c.fecha_revision).strftime('%d/%m/%Y %H:%M'),
                c.maquina.id_interno if c.maquina else '-',
                c.usuario.get_full_name() or c.usuario.username,
                estado_gen,
                c.comentarios or '-'
            ])

    elif tipo == 'ordenes':
        writer.writerow(['Estado', 'Fecha Salida', 'Fecha Llegada', 'Máquina', 'Operador', 'Nro Guía', 'Medida Salida', 'Medida Entrada'])
        ordenes = OrdenTrabajo.objects.filter(empresa=request.empresa).select_related('maquina', 'operador').order_by('-fecha_salida')
        for o in ordenes:
            estado = 'Cerrada' if o.fecha_entrada else 'En Ruta'
            fecha_out = timezone.localtime(o.fecha_salida).strftime('%d/%m/%Y %H:%M') if o.fecha_salida else '-'
            fecha_in = timezone.localtime(o.fecha_entrada).strftime('%d/%m/%Y %H:%M') if o.fecha_entrada else '-'
            writer.writerow([
                estado,
                fecha_out,
                fecha_in,
                o.maquina.id_interno if o.maquina else '-',
                o.operador.get_full_name() or o.operador.username,
                o.nro_guia_despacho or '-',
                o.medida_salida,
                o.medida_entrada if o.medida_entrada else '-'
            ])
            
    else:
        # Prevención contra errores 404 (Tipos errados)
        writer.writerow(['Error', 'Tipo de exportación no soportado por el sistema.'])

    return response
