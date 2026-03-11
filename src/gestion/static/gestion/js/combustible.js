// =========================================================================
//   MaqLogik - Lógica JS del Módulo Combustible
//   =========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // =====================================================================
    //  UI DINÁMICA: Campos condicionales según Tipo de Carga
    //  INTERNA: Maquina, Operador, Litros, OT, Sello Flujómetro
    //  EXTERNA: Maquina, Operador, Litros, OT, Precio Litro, Costo Total, Tipo Doc, N° Doc
    // =====================================================================
    const tipoSelect = document.getElementById('tipo_carga_select');
    
    // Grupos COMUNES: siempre visibles tras elegir tipo
    const gruposComunes = [
        'group_orden_trabajo',
        'group_maquina',
        'group_operador',
        'group_litros',
        'group_medida_al_cargar',
    ];

    // Grupos exclusivos de INTERNA
    const gruposInterna = [
        'group_sello_flujometro',
    ];

    // Grupos exclusivos de EXTERNA
    const gruposExterna = [
        'group_tipo_documento',
        'group_numero_documento',
        'group_precio_unitario',
        'group_costo_total',
    ];

    // Nodos para Auto-Cálculo
    const cantidadLitros = document.getElementById('litros_input');
    const precioLitro = document.getElementById('precio_unitario_input');
    const totalPago = document.getElementById('costo_total_input');

    function setVisible(ids, visible) {
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = visible ? '' : 'none';
        });
    }

    function toggleFields() {
        if (!tipoSelect) return;
        const tipo = tipoSelect.value;

        if (!tipo) {
            // Nada seleccionado: ocultar todo excepto el selector
            setVisible(gruposComunes, false);
            setVisible(gruposInterna, false);
            setVisible(gruposExterna, false);
            return;
        }

        // Mostrar campos comunes
        setVisible(gruposComunes, true);

        if (tipo === 'INTERNA') {
            setVisible(gruposInterna, true);
            setVisible(gruposExterna, false);
        } else { // EXTERNA
            setVisible(gruposInterna, false);
            setVisible(gruposExterna, true);
        }
    }

    function calculateTotal() {
        if (cantidadLitros && precioLitro && totalPago && tipoSelect && tipoSelect.value === 'EXTERNA') {
            const lts = parseFloat(cantidadLitros.value) || 0;
            const precio = parseFloat(precioLitro.value) || 0;
            if (lts > 0 && precio > 0) {
                totalPago.value = Math.round(lts * precio);
            } else {
                totalPago.value = '';
            }
        }
    }

    if (tipoSelect) {
        // Select2 emite eventos jQuery, no nativos, por eso usamos jQuery .on()
        if (typeof $ !== 'undefined') {
            $('#tipo_carga_select').on('change', function() {
                toggleFields();
                calculateTotal();
            });
        } else {
            // Fallback por si jQuery no cargó aún
            tipoSelect.addEventListener('change', () => {
                toggleFields();
                calculateTotal();
            });
        }
        // Ejecutar al cargar para respetar el valor inicial (cuando hay error de validación y se vuelve al form)
        toggleFields();
    }

    // Bind Auto-Cálculo Events
    if (cantidadLitros && precioLitro) {
        cantidadLitros.addEventListener('input', calculateTotal);
        precioLitro.addEventListener('input', calculateTotal);
    }


    // Auto-Asignación de OT Abierta
    const maquinaSelect = document.getElementById('id_maquina');
    const otSelect = document.getElementById('id_orden_trabajo');
    const operadorSelect = document.getElementById('id_operador'); // Select del Operador

    if (maquinaSelect && otSelect) {
        // Select2 en maquina también emite evento jQuery
        $('#id_maquina').on('change', function() {
            const maquinaId = this.value;
            if (!maquinaId) return;

            fetch(`/api/combustible/maquina/${maquinaId}/ot_abierta/`)
                .then(response => response.json())
                .then(data => {
                    // ─── 1. Auto-seleccionar la OT más reciente ───
                    if (data.ot_id) {
                        $(otSelect).val(data.ot_id).trigger('change'); // Notificar a Select2
                        highlightField(otSelect, 'green');
                    } else {
                        $(otSelect).val('').trigger('change');
                    }

                    // ─── 2. Auto-seleccionar Operador (OT tiene prioridad; fallback = operador fijo de la máquina) ───
                    if (data.operador_id && operadorSelect) {
                        $(operadorSelect).val(data.operador_id).trigger('change'); // Notificar a Select2
                        highlightField(operadorSelect, 'green');
                    }

                    // ─── 3. Auto-rellenar Medida (Horómetro/Km) ───
                    const medidaInput = document.getElementById('id_medida_al_cargar');
                    if (medidaInput && data.medida_actual !== undefined && data.medida_actual !== '') {
                        medidaInput.value = data.medida_actual;
                        // Actualizar placeholder con la unidad correcta (Km o Hr)
                        if (data.unidad_label) {
                            medidaInput.placeholder = `Registro actual de la máquina (${data.unidad_label})`;
                        }
                        highlightField(medidaInput, 'blue');
                    }
                })
                .catch(err => console.error("Error al obtener datos de la máquina:", err));
        });
    }

    function highlightField(el, color) {
        if (!el) return;
        const colors = {
            green: { border: '#10b981', shadow: 'rgba(16, 185, 129, 0.5)' },
            blue:  { border: '#3b82f6', shadow: 'rgba(59, 130, 246, 0.5)' }
        };
        const c = colors[color] || colors.green;
        el.style.transition = 'border-color 0.3s, box-shadow 0.3s';
        el.style.borderColor = c.border;
        el.style.boxShadow = `0 0 5px ${c.shadow}`;
        setTimeout(() => {
            el.style.borderColor = '';
            el.style.boxShadow = '';
        }, 2500);
    }

    // Autocálculo para Compra de Combustible (Facturas a Proveedor)
    const cantidadLitrosCompra = document.getElementById('cantidad_litros');
    const precioLitroCompra = document.getElementById('precio_litro');
    const totalPagoCompra = document.getElementById('total_pago');

    function calculateTotalCompra() {
        if (cantidadLitrosCompra && precioLitroCompra && totalPagoCompra) {
            const lts = parseFloat(cantidadLitrosCompra.value) || 0;
            const precio = parseFloat(precioLitroCompra.value) || 0;
            if (lts > 0 && precio > 0) {
                totalPagoCompra.value = Math.round(lts * precio);
            }
        }
    }

    if (cantidadLitrosCompra && precioLitroCompra) {
        cantidadLitrosCompra.addEventListener('input', calculateTotalCompra);
        precioLitroCompra.addEventListener('input', calculateTotalCompra);
    }
});
