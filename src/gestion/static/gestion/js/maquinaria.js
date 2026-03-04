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
        if (unidad === 'HORAS') {
            // Generalmente según fabricante son 200 horas, el usuario indicó diferencia de 200 en el ejemplo (125 a 325 es 200, pero el estandar general es sumar +200). Usaremos un estandar de +200 o lo que calculó matematicamente + 200. Vamos a sumar 200 horas como estándar y 10000 en KMS. 
            // Espera, el usuario dijo: "si (...) se ingresa 125 horas que el campo (...) muestre 325". Esto es literalmente sumar 200.
            inputProximo.value = (valorActual + 200).toFixed(1);
        } else if (unidad === 'KM') {
            inputProximo.value = (valorActual + 10000).toFixed(1);
        } else {
            inputProximo.value = '';
        }
    }

    if (inputActual && inputUnidad) {
        inputActual.addEventListener('input', recalcularMantenimiento);
        inputUnidad.addEventListener('change', recalcularMantenimiento);
    }

});
