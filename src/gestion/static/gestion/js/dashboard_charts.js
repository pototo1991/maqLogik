document.addEventListener('DOMContentLoaded', function() {
    // Validar que existan los datos exportados por el json_script (Solo para DUEÑOS/CHIFF)
    const fechasDataEl = document.getElementById('fechas-data');
    if (!fechasDataEl) return;

    const dates = JSON.parse(fechasDataEl.textContent);
    const ots = JSON.parse(document.getElementById('ots-data').textContent);
    
    // Calcular Disponibles
    const total = JSON.parse(document.getElementById('total-data').textContent);
    const enRuta = JSON.parse(document.getElementById('ruta-data').textContent);
    const enTaller = JSON.parse(document.getElementById('taller-data').textContent);
    const disponibles = total - enRuta - enTaller;

    // Gráfico 1: Área (Tendencia de Órdenes de Trabajo)
    var optionsOts = {
        series: [{
            name: 'Órdenes Creadas',
            data: ots
        }],
        chart: { type: 'area', height: 250, toolbar: { show: false }, background: 'transparent', fontFamily: 'Inter, sans-serif' },
        stroke: { curve: 'smooth', width: 2 },
        fill: {
            type: 'gradient',
            gradient: { shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.1, stops: [0, 90, 100] }
        },
        dataLabels: { enabled: false },
        xaxis: { categories: dates, labels: { style: { colors: '#9ca3af' } } },
        yaxis: { labels: { style: { colors: '#d1d5db' } } },
        theme: { mode: 'dark' },
        colors: ['#3b82f6'] // Blue Accent
    };
    
    var otsChartContainer = document.querySelector("#otsChart");
    if(otsChartContainer) {
        var otsChart = new ApexCharts(otsChartContainer, optionsOts);
        otsChart.render();
    }
    
    // Gráfico 2: Donut (Distribución de la Flota)
    var optionsFlota = {
        series: [disponibles, enRuta, enTaller],
        chart: { type: 'donut', height: 250, background: 'transparent', fontFamily: 'Inter, sans-serif' },
        labels: ['Disponibles Base', 'En Terreno/Ruta', 'En Taller'],
        colors: ['#10b981', '#fbbf24', '#ef4444'], // Green, Orange, Red
        theme: { mode: 'dark' },
        stroke: { show: true, colors: ['#0f172a'], width: 2 },
        dataLabels: { enabled: true, dropShadow: { enabled: false } },
        legend: { position: 'bottom', labels: { colors: '#d1d5db' } }
    };
    
    var flotaChartContainer = document.querySelector("#flotaChart");
    if(flotaChartContainer) {
        var flotaChart = new ApexCharts(flotaChartContainer, optionsFlota);
        flotaChart.render();
    }

    // Gráfico 3: Consumo Combustible (Area)
    const combustibleDataEl = document.getElementById('combustible-data');
    if (combustibleDataEl) {
        const combustibleData = JSON.parse(combustibleDataEl.textContent);
        var optionsCombustible = {
            series: [{
                name: 'Consumo (Lts)',
                data: combustibleData
            }],
            chart: { type: 'area', height: 250, toolbar: { show: false }, background: 'transparent', fontFamily: 'Inter, sans-serif' },
            stroke: { curve: 'smooth', width: 2 },
            fill: {
                type: 'gradient',
                gradient: { shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.1, stops: [0, 90, 100] }
            },
            dataLabels: { enabled: false },
            xaxis: { categories: dates, labels: { style: { colors: '#9ca3af' } } },
            yaxis: { labels: { style: { colors: '#d1d5db' } } },
            theme: { mode: 'dark' },
            colors: ['#10b981'] // Emerald Green
        };
        var combustibleChartContainer = document.querySelector("#combustibleChart");
        if(combustibleChartContainer) {
            var combustibleChart = new ApexCharts(combustibleChartContainer, optionsCombustible);
            combustibleChart.render();
        }
    }

    // Gráfico 4: Costos de Mantención (Bar)
    const costosDataEl = document.getElementById('costos-data');
    if (costosDataEl) {
        const costosData = JSON.parse(costosDataEl.textContent);
        var optionsCostos = {
            series: [{
                name: 'Costo (CLP/USD)',
                data: costosData
            }],
            chart: { type: 'bar', height: 250, toolbar: { show: false }, background: 'transparent', fontFamily: 'Inter, sans-serif' },
            plotOptions: {
                bar: { borderRadius: 4, horizontal: false, columnWidth: '50%' }
            },
            dataLabels: { enabled: false },
            xaxis: { categories: dates, labels: { style: { colors: '#9ca3af' } } },
            yaxis: { 
                labels: { 
                    style: { colors: '#d1d5db' },
                    formatter: function (val) { return "$" + val.toLocaleString(); }
                } 
            },
            theme: { mode: 'dark' },
            colors: ['#f59e0b'] // Amber
        };
        var costosChartContainer = document.querySelector("#costosChart");
        if(costosChartContainer) {
            var costosChart = new ApexCharts(costosChartContainer, optionsCostos);
            costosChart.render();
        }
    }
});
