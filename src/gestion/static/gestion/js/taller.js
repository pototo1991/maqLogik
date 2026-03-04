// Lógica global para Módulo Taller y Mantenimiento

document.addEventListener('DOMContentLoaded', function() {
    // ============================================
    // VISTA: ot_form.html (Apertura de Orden de Taller)
    // ============================================
    
    // Auto-completado de horómetros según la máquina seleccionada
    const maquinaSelect = document.getElementById('id_maquina');
    const medidaInput = document.getElementById('id_medida_ingreso');
    const medidasMapData = document.getElementById('medidas-map-data');

    if (maquinaSelect && medidaInput && medidasMapData) {
        const medidasMap = JSON.parse(medidasMapData.textContent);
        
        maquinaSelect.addEventListener('change', function() {
            const mapId = this.value;
            if(mapId && medidasMap[mapId]) {
                medidaInput.value = medidasMap[mapId];
            } else {
                medidaInput.value = '';
            }
        });
    }
});
