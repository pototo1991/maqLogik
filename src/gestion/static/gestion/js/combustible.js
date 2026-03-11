// =========================================================================
//   MaqLogik - Lógica JS del Módulo Combustible
//   =========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // UI Logic for CombustibleLogForm
    const tipoSelect = document.getElementById('tipo_carga_select');
    const precioUnitarioGroup = document.getElementById('group_precio_unitario');
    const costoTotalGroup = document.getElementById('group_costo_total');
    
    // Nuevos campos de facturación (si existen en el DOM)
    const tipoDocGroup = document.getElementById('group_tipo_documento');
    const numDocGroup = document.getElementById('group_numero_documento');
    
    // Campo de Sello del Flujómetro (Obligatorio en Interna)
    const selloFlujometroGroup = document.getElementById('group_sello_flujometro');

    // Nodos para Auto-Cálculo
    const cantidadLitros = document.getElementById('litros_input');
    const precioLitro = document.getElementById('precio_unitario_input');
    const totalPago = document.getElementById('costo_total_input');
    
    function toggleFields() {
        if (!tipoSelect || !precioUnitarioGroup || !costoTotalGroup) return;

        if (tipoSelect.value === 'INTERNA') {
            precioUnitarioGroup.classList.add('hidden');
            costoTotalGroup.classList.add('hidden');
            if (tipoDocGroup) tipoDocGroup.classList.add('hidden');
            if (numDocGroup) numDocGroup.classList.add('hidden');
            if (selloFlujometroGroup) selloFlujometroGroup.classList.remove('hidden'); // MOSTRAR Sello
        } else {
            precioUnitarioGroup.classList.remove('hidden');
            costoTotalGroup.classList.remove('hidden');
            if (tipoDocGroup) tipoDocGroup.classList.remove('hidden');
            if (numDocGroup) numDocGroup.classList.remove('hidden');
            if (selloFlujometroGroup) selloFlujometroGroup.classList.add('hidden'); // OCULTAR Sello
        }
    }

    function calculateTotal() {
        if (cantidadLitros && precioLitro && totalPago && tipoSelect.value === 'EXTERNA') {
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
        tipoSelect.addEventListener('change', () => {
            toggleFields();
            calculateTotal(); // recalcular por si acaso
        });
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
        maquinaSelect.addEventListener('change', function() {
            const maquinaId = this.value;
            if (!maquinaId) return;

            // Consultar a la API si hay una OT Abierta para esta máquina
            fetch(`/api/combustible/maquina/${maquinaId}/ot_abierta/`)
                .then(response => response.json())
                .then(data => {
                    if (data.ot_id) {
                        otSelect.value = data.ot_id;
                        // Destacar visualmente el cambio automático en OT
                        otSelect.style.transition = 'border-color 0.3s, box-shadow 0.3s';
                        otSelect.style.borderColor = '#10b981';
                        otSelect.style.boxShadow = '0 0 5px rgba(16, 185, 129, 0.5)';
                        
                        // Si nos viene el operador de la OT, auto-asignarlo también
                        if (data.operador_id && operadorSelect) {
                            operadorSelect.value = data.operador_id;
                            operadorSelect.style.transition = 'border-color 0.3s, box-shadow 0.3s';
                            operadorSelect.style.borderColor = '#10b981';
                            operadorSelect.style.boxShadow = '0 0 5px rgba(16, 185, 129, 0.5)';
                        }

                        // Auto-rellenar Medida Actual (Horómetro/Km)
                        const medidaInput = document.getElementById('id_medida_al_cargar');
                        if (medidaInput && data.medida_actual !== undefined) {
                            medidaInput.value = data.medida_actual;
                            // Efecto visual azul para las medidas numéricas
                            medidaInput.style.transition = 'border-color 0.3s, box-shadow 0.3s';
                            medidaInput.style.borderColor = '#3b82f6';
                            medidaInput.style.boxShadow = '0 0 5px rgba(59, 130, 246, 0.5)';
                        }

                        setTimeout(() => {
                            otSelect.style.borderColor = '';
                            otSelect.style.boxShadow = '';
                            if (operadorSelect) {
                                operadorSelect.style.borderColor = '';
                                operadorSelect.style.boxShadow = '';
                            }
                            if (medidaInput) {
                                medidaInput.style.borderColor = '';
                                medidaInput.style.boxShadow = '';
                            }
                        }, 2000);
                    } else {
                        // Si no hay OT abierta, dejar OT en blanco
                        otSelect.value = '';
                        
                        // Pero de igual modo, si la API nos devolvió la medida, inyectarla
                        const medidaInput = document.getElementById('id_medida_al_cargar');
                        if (medidaInput && data.medida_actual !== undefined && data.medida_actual !== '') {
                            medidaInput.value = data.medida_actual;
                            medidaInput.style.transition = 'border-color 0.3s, box-shadow 0.3s';
                            medidaInput.style.borderColor = '#3b82f6';
                            medidaInput.style.boxShadow = '0 0 5px rgba(59, 130, 246, 0.5)';
                            setTimeout(() => {
                                medidaInput.style.borderColor = '';
                                medidaInput.style.boxShadow = '';
                            }, 2000);
                        }
                    }
                })
                .catch(err => console.error("Error al obtener OT:", err));
        });
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
