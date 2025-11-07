document.addEventListener('DOMContentLoaded', async () => {
    const contenedor = document.getElementById("menu");

    const cargarproductos = async () => {
        try {
            const response = await fetch("http://127.0.0.1:8000/menu/salchipapas");
            if (!response.ok) throw new Error(`Error ${response.status}`);

            const productos = await response.json();
            contenedor.innerHTML = "";

            if (productos.length === 0) {
                contenedor.innerHTML = `<p class="text-center text-muted">No hay productos en esta categoría.</p>`;
                return;
            }

            productos.forEach(prod => {
                const card = document.createElement("div");
                card.className = "col";

                card.innerHTML = `
                    <div class="card h-100 bg-dark text-white border-0 shadow">
                        <img src="${prod.imagen || 'https://via.placeholder.com/300x180'}" 
                             class="card-img-top" 
                             alt="${prod.nombre}">
                        <div class="card-body text-center">
                            <h5 class="card-title text-carts">${prod.nombre}</h5>
                            <p class="card-text">${prod.descripcion || ''}</p>
                            <p class="fw-bold text-white">$${prod.precio}</p>
                        </div>
                    </div>
                `;
                contenedor.appendChild(card);
            });
        } catch (error) {
            console.error("Error al cargar los productos de Chorizos:", error);
            contenedor.innerHTML = `<p class="text-center text-danger">Error al cargar los productos.</p>`;
        }
    };

    cargarproductos();
});
