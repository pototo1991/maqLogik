// =========================================================================
//   MaqLogik - Lógica JS del Módulo Órdenes de Trabajo (OTs)
// =========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Escuchar el evento de selección de la Máquina en el Formulario de la OT
    const selectMaquina = document.getElementById('id_maquina');
    const selectOperador = document.getElementById('id_operador');
    const inputMedidaSalida = document.getElementById('id_medida_salida');

    const operadoresData = document.getElementById('operadores-map-data');
    const medidasData = document.getElementById('medidas-map-data');
    
    let operadoresMapOT = {};
    let medidasMapOT = {};

    if (operadoresData) {
        operadoresMapOT = JSON.parse(operadoresData.textContent || "{}");
    }
    if (medidasData) {
        medidasMapOT = JSON.parse(medidasData.textContent || "{}");
    }

    if (selectMaquina) {
        // Usar jQuery para escuchar el evento 'change' porque Select2 emite eventos jQuery
        $('#id_maquina').on('change', function() {
            const maquinaId = this.value;
            
            // 1. Auto-asignar Operador
            if (selectOperador && Object.keys(operadoresMapOT).length >= 0) {
                if (maquinaId && operadoresMapOT[maquinaId]) {
                    // Si Select2 está activo en el selector de operador, hay que actualizarlo vía jQuery
                    if ($(selectOperador).hasClass('select2-hidden-accessible')) {
                        $(selectOperador).val(operadoresMapOT[maquinaId]).trigger('change');
                    } else {
                        selectOperador.value = operadoresMapOT[maquinaId];
                    }
                    selectOperador.style.transition = 'border-color 0.3s, box-shadow 0.3s';
                    selectOperador.style.borderColor = '#10b981';
                    selectOperador.style.boxShadow = '0 0 5px rgba(16, 185, 129, 0.5)';
                    setTimeout(() => {
                        selectOperador.style.borderColor = '';
                        selectOperador.style.boxShadow = '';
                    }, 2000);
                } else {
                    if ($(selectOperador).hasClass('select2-hidden-accessible')) {
                        $(selectOperador).val('').trigger('change');
                    } else {
                        selectOperador.value = '';
                    }
                }
            }

            // 2. Auto-rellenar Medida de Salida (Horómetro / Km actual)
            if (inputMedidaSalida && Object.keys(medidasMapOT).length >= 0) {
                if (maquinaId && medidasMapOT[maquinaId] !== undefined) {
                    inputMedidaSalida.value = medidasMapOT[maquinaId];
                    // Efecto visual azul
                    inputMedidaSalida.style.transition = 'border-color 0.3s, box-shadow 0.3s';
                    inputMedidaSalida.style.borderColor = '#3b82f6'; 
                    inputMedidaSalida.style.boxShadow = '0 0 5px rgba(59, 130, 246, 0.5)';
                    setTimeout(() => {
                        inputMedidaSalida.style.borderColor = '';
                        inputMedidaSalida.style.boxShadow = '';
                    }, 2000);
                } else {
                    inputMedidaSalida.value = '';
                }
            }
        });
    }
});
