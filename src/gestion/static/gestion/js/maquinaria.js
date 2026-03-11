/**
 * maquinaria.js
 * Lógica de interfaz para los formularios de Maquinaria.
 */

document.addEventListener('DOMContentLoaded', function () {

    // Deshabilitar las opciones placeholder (valor vacío "") en todos los Select del formulario
    // para que actúen como un placeholder real y no sean seleccionables por el usuario.
    document.querySelectorAll('select.form-input').forEach(function (select) {
        var placeholder = select.querySelector('option[value=""]');
        if (placeholder) {
            placeholder.disabled = true;
        }
    });

    // Autocompletado de Próximo Mantenimiento
    const inputUnidad = document.getElementById('id_unidad_medida');
    const inputActual = document.getElementById('id_valor_actual_medida');
    const inputProximo = document.getElementById('id_proximo_mantenimiento');

    function recalcularMantenimiento() {
        if (!inputActual || !inputProximo || !inputUnidad) return;
        
        const valorActual = parseFloat(inputActual.value);
        if (isNaN(valorActual)) {
            inputProximo.value = '';
            return;
        }

        const unidad = inputUnidad.value;
        
        // Obtener la configuración dinámica de la empresa, o usar defaults de seguridad
        const limiteHoras = window.CONFIG_MANTENCION_HORAS || 200;
        const limiteKm = window.CONFIG_MANTENCION_KM || 10000;

        if (unidad === 'HORAS') {
            inputProximo.value = (valorActual + limiteHoras).toFixed(1);
        } else if (unidad === 'KM') {
            inputProximo.value = (valorActual + limiteKm).toFixed(1);
        } else {
            inputProximo.value = '';
        }
    }

    if (inputActual && inputUnidad) {
        inputActual.addEventListener('input', recalcularMantenimiento);
        inputUnidad.addEventListener('change', recalcularMantenimiento);
    }

});
