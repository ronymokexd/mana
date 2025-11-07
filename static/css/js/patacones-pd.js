document.addEventListener('DOMContentLoaded', async () => {
    const contenedor = document.getElementById("menu");

    const cargarproductos = async () => {
        try {
            const response = await fetch("https://mana-51g3.onrender.com//menu/patacones");
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
                            <button class="btn btn-warning agregar-carrito" 
                                data-id="${prod.id}" 
                                data-nombre="${prod.nombre}" 
                                data-precio="${prod.precio}">
                                Agregar al carrito
                            </button>
                        </div>
                    </div>
                `;
                contenedor.appendChild(card);
            });

            // Escuchar los botones del carrito
            document.querySelectorAll('.agregar-carrito').forEach(boton => {
                boton.addEventListener('click', e => {
                    const producto = {
                        id: e.target.dataset.id,
                        nombre: e.target.dataset.nombre,
                        precio: parseFloat(e.target.dataset.precio),
                        cantidad: 1
                    };
                    agregarAlCarrito(producto);
                });
            });

        } catch (error) {
            console.error("Error al cargar los productos de patacones:", error);
            contenedor.innerHTML = `<p class="text-center text-danger">Error al cargar los productos.</p>`;
        }
    };

    const agregarAlCarrito = (producto) => {
        let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
        const existe = carrito.find(item => item.id === producto.id);
        if (existe) {
            existe.cantidad++;
        } else {
            carrito.push(producto);
        }
        localStorage.setItem("carrito", JSON.stringify(carrito));
        alert(`✅ ${producto.nombre} agregado al carrito`);
    };

    cargarproductos();
});
