from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from ..models import InventarioCombustible, CompraCombustible, CombustibleLog
from ..forms import CompraCombustibleForm, CombustibleLogForm
from ..utils import modulo_requerido
import logging

logger = logging.getLogger(__name__)

@login_required(login_url='web_login')
@modulo_requerido('modulo_combustible')
def combustible_dashboard(request):
    # Asegurar que la empresa tenga su Inventario creado
    inventario, created = InventarioCombustible.objects.get_or_create(empresa=request.empresa)
    
    compras_recientes = CompraCombustible.objects.filter(empresa=request.empresa).order_by('-fecha_compra')[:5]
    cargas_recientes = CombustibleLog.objects.filter(empresa=request.empresa).order_by('-id')[:5]
    
    return render(request, 'gestion/combustible/dashboard.html', {
        'inventario': inventario,
        'compras': compras_recientes,
        'cargas': cargas_recientes,
    })

@login_required
@transaction.atomic
def compra_create(request):
    """
    Registra una factura de compra de combustible, sumando litros al inventario 
    y recalculando el Precio Promedio Ponderado (PPP).
    """
    inventario, _ = InventarioCombustible.objects.get_or_create(empresa=request.empresa)
    
    if request.method == 'POST':
        form = CompraCombustibleForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.empresa = request.empresa
            compra.save()
            
            # --- Cálculo de PPP y actualización de Stock ---
            litros_nuevos = compra.cantidad_litros
            pago_nuevo = compra.total_pago
            
            # Valor total del inventario antiguo (litros * precio promedio anterior)
            valor_inventario_antiguo = inventario.stock_actual * inventario.precio_promedio_ponderado
            
            # Nuevo Coste Total = Coste Anterior + Coste de la nueva Factura
            costo_total_acumulado = valor_inventario_antiguo + pago_nuevo
            # Nuevo Stock
            nuevo_stock = inventario.stock_actual + litros_nuevos
            
            # Nuevo PPP
            if nuevo_stock > 0:
                inventario.precio_promedio_ponderado = costo_total_acumulado / nuevo_stock
            
            inventario.stock_actual = nuevo_stock
            inventario.save()
            
            logger.info('COMPRA combustible ID=%s. Litros=%s. PPP nuevo=%.2f. Usuario=%s. Empresa=%s.',
                        compra.pk, litros_nuevos, inventario.precio_promedio_ponderado,
                        request.user.username, request.empresa.id)
            messages.success(request, f'¡Reabastecimiento registrado exitosamente! Nuevo stock: {inventario.stock_actual} Lts.')
            return redirect('combustible_dashboard')
    else:
        # El input datetime-local requiere el formato YYYY-MM-DDTHH:MM
        form = CompraCombustibleForm(initial={'fecha_compra': timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')})
        
    return render(request, 'gestion/combustible/form_general.html', {
        'form': form,
        'titulo': 'Ingresar Factura de Combustible',
        'subtitulo': 'Reabastecer el tanque principal y ajustar Precio Promedio.',
    })

@login_required
@transaction.atomic
def carga_create(request):
    """
    Registra que una máquina fue abastecida. Si es interna, se descuenta stock.
    """
    inventario, _ = InventarioCombustible.objects.get_or_create(empresa=request.empresa)
    
    if request.method == 'POST':
        form = CombustibleLogForm(request.POST, empresa=request.empresa)
        
        # Validar lógica de stock manualmente antes de intentar guardado del form general si requiere
        if form.is_valid():
            carga = form.save(commit=False)
            carga.empresa = request.empresa
            
            tipo = carga.tipo_carga
            litros_req = carga.litros
            
            if tipo == 'INTERNA':
                if inventario.stock_actual < litros_req:
                    messages.error(request, f'Stock insuficiente. Intenta cargar {litros_req} Lts, pero solo quedan {inventario.stock_actual} Lts en Patio.')
                    return render(request, 'gestion/combustible/form_general.html', {'form': form, 'titulo': 'Abastecer Maquinaria', 'es_carga': True})
                
                # Descontar stock
                inventario.stock_actual -= litros_req
                inventario.save()
                
                # Calcular costos con el Precio Promedio del Inventario
                carga.precio_unitario = inventario.precio_promedio_ponderado
                carga.costo_total = litros_req * carga.precio_unitario
                
            elif tipo == 'EXTERNA':
                # En cargas externas el usuario debe indicar cuanto pagó (precio unitario o costo total debe venir en form)
                if not carga.precio_unitario or not carga.costo_total:
                    messages.error(request, 'Para recargas EXTERNAS, debes proporcionar el Precio Unitario y Costo Total facturado.')
                    return render(request, 'gestion/combustible/form_general.html', {'form': form, 'titulo': 'Abastecer Maquinaria', 'es_carga': True})
                
                # (No tocamos el inventario)
            
            # Se guarda el log consolidado
            carga.save()
            logger.info('CARGA combustible ID=%s. Tipo=%s. Litros=%s. Maquina=%s. Usuario=%s. Empresa=%s.',
                        carga.pk, tipo, litros_req, carga.maquina_id, request.user.username, request.empresa.id)
            messages.success(request, f'Carga de {litros_req} Lts. ("{tipo}") registrada existosamente para {carga.maquina.id_interno}.')
            return redirect('combustible_dashboard')
        else:
            messages.error(request, 'Revise los datos ingresados.')
    else:
        form = CombustibleLogForm(empresa=request.empresa)
        
    return render(request, 'gestion/combustible/form_general.html', {
        'form': form,
        'titulo': 'Registrar Abastecimiento (Máquina)',
        'subtitulo': 'Detalla el llenado de estanque. Para las cargas INTERNAS el costo y precio se aplicarán solos.',
        'es_carga': True
    })

@login_required
def api_ot_abierta(request, maquina_id):
    """
    Retorna el ID de la última Orden de Trabajo registrada para la 
    máquina solicitada (abierta o cerrada recién), permitiendo al frontend auto-seleccionarla.
    """
    from ..models import OrdenTrabajo, Maquinaria
    
    # Obtener el id_interno de la maquina
    maquina = Maquinaria.objects.filter(id=maquina_id).first()
    medida_actual = float(maquina.valor_actual_medida) if maquina and maquina.valor_actual_medida else ''
    
    ot_abierta = OrdenTrabajo.objects.filter(
        empresa=request.empresa,
        maquina_id=maquina_id
    ).order_by('-id').first()
    
    if ot_abierta:
        return JsonResponse({
            'ot_id': ot_abierta.id,
            'operador_id': ot_abierta.operador.id if ot_abierta.operador else None,
            'medida_actual': medida_actual
        })
    return JsonResponse({'ot_id': None, 'operador_id': None, 'medida_actual': medida_actual})
