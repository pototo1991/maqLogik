/**
 * MaqLogik - Script de Gestión de Formularios de Checklist y Firma Digital Canvas
 */

document.addEventListener("DOMContentLoaded", function() {

    // 1. AUTOCOMPLETADO DE OPERADOR
    const selectMaquina = document.getElementById('id_maquina');
    if (selectMaquina && typeof operadoresMapContext !== 'undefined' && operadoresMapContext) {
        try {
            const mapOperator = JSON.parse(operadoresMapContext);
            selectMaquina.addEventListener('change', function() {
                const maquinaId = this.value;
                if (mapOperator[maquinaId]) {
                    // Si el sistema tuviera select de operador, podríamos rellenarlo aquí.
                    // Actualmente, el operador se asigna por request.user al hacer post en la vista.
                    console.log(`Operador esperado fijo para la máquina elegida: ${mapOperator[maquinaId]}`);
                }
            });
        } catch (e) {
            console.error("No se pudo parsear el diccionario de operadores móviles", e);
        }
    }
});
