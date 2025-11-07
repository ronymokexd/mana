async function cargarEstadisticasGraficos() {
    try {
        const response = await fetch("https://mana-51g3.onrender.com/estadisticas_dia");
        if (!response.ok) throw new Error("Error al obtener estadísticas");
        const stats = await response.json();

        // 🔹 Productos por Categoría (barra)
        const categorias = stats.productos_por_categoria.map(c => c.categoria);
        const cantidades = stats.productos_por_categoria.map(c => c.total);

        new Chart(document.getElementById('productosCategoriaChart'), {
            type: 'bar',
            data: {
                labels: categorias,
                datasets: [{
                    label: 'Cantidad vendida',
                    data: cantidades,
                    backgroundColor: '#4bc0c0'
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });

        // 🔹 Producto Más Vendido (circular) con nombre + categoría
        const prod = stats.producto_mas_vendido;
        new Chart(document.getElementById('productoMasVendidoChart'), {
            type: 'doughnut',
            data: {
                labels: [`${prod.nombre} (${prod.categoria})`, 'Otros Productos'],
                datasets: [{
                    data: [prod.cantidad, stats.total_pedidos - prod.cantidad],
                    backgroundColor: ['#ffcd56', '#2a2a2a']
                }]
            },
            options: { responsive: true }
        });

        // 🔹 Método de Pago Más Usado (circular)
        new Chart(document.getElementById('metodoPagoChart'), {
            type: 'doughnut',
            data: {
                labels: [stats.metodo_pago_mas_usado, 'Otros Métodos'],
                datasets: [{
                    data: [stats.total_pedidos, 0],
                    backgroundColor: ['#36a2eb', '#2a2a2a']
                }]
            },
            options: { responsive: true }
        });

    } catch (error) {
        console.error("Error al cargar estadísticas:", error);
    }
}

window.onload = cargarEstadisticasGraficos;
