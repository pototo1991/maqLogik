document.addEventListener('DOMContentLoaded', function() {
    // Datos inyectados desde Django via json_script
    const activasEl = document.getElementById('activas-data');
    if (!activasEl) return;

    const activas = JSON.parse(activasEl.textContent);
    const inactivas = JSON.parse(document.getElementById('inactivas-data').textContent);
    const modulosData = JSON.parse(document.getElementById('modulos-data').textContent);

    // Gráfico de Barras: Módulos
    var optionsModulos = {
        series: [{
            name: 'Empresas Suscritas',
            data: modulosData
        }],
        chart: { type: 'bar', height: 250, toolbar: { show: false }, background: 'transparent', fontFamily: 'Inter, sans-serif' },
        plotOptions: { bar: { borderRadius: 4, horizontal: true } },
        dataLabels: { enabled: false },
        xaxis: { 
            categories: ['GPS Tracking', 'Taller Mecánico', 'Combustible', 'Checklists', 'Reportería PDF'],
            labels: { style: { colors: '#9ca3af' } }
        },
        yaxis: { labels: { style: { colors: '#d1d5db' } } },
        theme: { mode: 'dark' },
        colors: ['#3b82f6'] // Blue accent
    };
    
    var modulosChartContainer = document.querySelector("#modulosChart");
    if(modulosChartContainer) {
        var modulosChart = new ApexCharts(modulosChartContainer, optionsModulos);
        modulosChart.render();
    }

    // Gráfico de Dona: Empresas Activas/Inactivas
    var optionsEmpresas = {
        series: [activas, inactivas],
        chart: { type: 'donut', height: 250, background: 'transparent', fontFamily: 'Inter, sans-serif' },
        labels: ['Cuentas Activas', 'Cuentas Suspendidas'],
        colors: ['#10b981', '#ef4444'], // Green and Red
        theme: { mode: 'dark' },
        stroke: { show: true, colors: ['#0f172a'], width: 2 },
        dataLabels: { enabled: true, dropShadow: { enabled: false } },
        legend: { position: 'bottom', labels: { colors: '#d1d5db' } }
    };
    
    var empresasChartContainer = document.querySelector("#empresasChart");
    if(empresasChartContainer) {
        var empresasChart = new ApexCharts(empresasChartContainer, optionsEmpresas);
        empresasChart.render();
    }
});
