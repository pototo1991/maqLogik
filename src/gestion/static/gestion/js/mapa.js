// =========================================================================
//   MaqLogik - Script de Mapa GPS (Leaflet) y Polling Asíncrono
//   =========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar Mapa centrado en Chile por defecto (o lat/lng generica)
    const map = L.map('map').setView([-33.4489, -70.6693], 5);

    // Capa oscura de CartoDB (Dark Matter) - Gratuita y sin API KEY
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Diccionario para almacenar marcadores activos y no redibujar todo
    let activeMarkers = {};
    let activeListItems = {};

    // Iconos
    const iconActive = L.divIcon({ className: 'pulse-marker', iconSize: [15, 15] });
    const iconIdle = L.divIcon({ className: 'pulse-marker idle', iconSize: [15, 15] });

    // Obtenemos la URL de la API mediante un atributo global guardado en el DOM
    const apiUrl = document.getElementById('map-data-container').dataset.apiUrl;

    function fetchPositions() {
        if (!apiUrl) return;

        fetch(apiUrl)
            .then(response => response.json())
            .then(result => {
                if(result.status === 'success') {
                    const data = result.data;
                    let validPoints = [];
                    const listContent = document.getElementById('machine-list-content');

                    data.forEach(item => {
                        const latLng = [item.lat, item.lng];
                        validPoints.push(latLng);

                        const popupHtml = `
                            <div class="popup-title">${item.id_interno}</div>
                            <div class="popup-data">
                                <strong>Patente:</strong> ${item.patente || 'N/A'}<br>
                                <strong>Velocidad:</strong> ${item.velocidad.toFixed(1)} km/h<br>
                                <strong>Última act:</strong> ${item.fecha_hora}<br>
                                <strong>Estado:</strong> ${item.estado}
                            </div>
                            <span class="status-badge ${item.is_active ? 'status-active' : 'status-idle'}">
                                ${item.is_active ? 'EN MOVIMIENTO' : 'DETENIDO'}
                            </span>
                        `;

                        // 1. Manejo del Marcador en el Mapa
                        if(activeMarkers[item.id_maquina]) {
                            // Mover marcador existente
                            activeMarkers[item.id_maquina].setLatLng(latLng);
                            activeMarkers[item.id_maquina].getPopup().setContent(popupHtml);
                            activeMarkers[item.id_maquina].setIcon(item.is_active ? iconActive : iconIdle);
                        } else {
                            // Crear nuevo marcador
                            const marker = L.marker(latLng, { 
                                icon: item.is_active ? iconActive : iconIdle 
                            }).addTo(map);
                            
                            marker.bindPopup(popupHtml);
                            activeMarkers[item.id_maquina] = marker;
                        }

                        // 2. Manejo de la Lista en el Sidebar
                        if (listContent) {
                            let li = activeListItems[item.id_maquina];
                            const liHtml = `
                                <div style="display: flex; justify-content: space-between; align-items:center;">
                                    <div class="id-interno">${item.id_interno}</div>
                                    <span class="status-badge ${item.is_active ? 'status-active' : 'status-idle'}" style="margin:0; font-size:0.65rem;">
                                        ${item.is_active ? 'EN RUTA' : 'DETENIDA'}
                                    </span>
                                </div>
                                <div class="info">
                                    Patente: ${item.patente || 'N/A'}<br>
                                    Vel. Actual: ${item.velocidad.toFixed(1)} km/h
                                </div>
                            `;

                            if (!li) {
                                // Remover texto "Cargando_maquinas..." si existe
                                const loadingState = listContent.querySelector('.loading-state');
                                if (loadingState) loadingState.remove();

                                // Crear nuevo elemento
                                li = document.createElement('div');
                                li.className = 'machine-item';
                                
                                // Listener para "Hacer Zoom y Centrar"
                                li.addEventListener('click', () => {
                                    if(activeMarkers[item.id_maquina]) {
                                        const pos = activeMarkers[item.id_maquina].getLatLng();
                                        // flyTo crea un efecto visual de viaje asombroso
                                        map.flyTo(pos, 16, {animate: true, duration: 1.5});
                                        
                                        // Abrir su globito de texto cuando termine de volar
                                        setTimeout(() => {
                                             activeMarkers[item.id_maquina].openPopup();
                                        }, 1000);
                                    }
                                });
                                
                                listContent.appendChild(li);
                                activeListItems[item.id_maquina] = li;
                            }
                            // Actualizar info interna
                            li.innerHTML = liHtml;
                        }
                    });

                    // Si no hubo maquinas transmitiendo
                    if (data.length === 0 && listContent) {
                        listContent.innerHTML = '<div style="color: #6b7280; text-align: center; margin-top: 20px;">No hay señales GPS recientes.</div>';
                    }
                }
            })
            .catch(err => console.error("Error trayendo GPS:", err));
    }

    // Llamada inicial
    fetchPositions();

    // Loop cada 5 segundos
    setInterval(fetchPositions, 5000);
});
