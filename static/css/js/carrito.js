// Obtener carrito y datos del cliente desde localStorage
let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
let cliente = JSON.parse(localStorage.getItem("cliente"));

// Contenedor principal
const contenedor = document.querySelector(".d-flex");

// Mostrar carrito
function mostrarCarrito() {
    contenedor.innerHTML = `
        <img src="../img/mana.png" alt="logo" style="width: 200px; height: auto; margin-bottom: 20px;">
        <h3 class="text-white mb-3">Tu carrito</h3>
        <div class="w-100 bg-light rounded-3 p-3">
            ${carrito.length === 0 ? 
                "<p class='text-center'>No hay productos en el carrito.</p>" : 
                carrito.map((p, i) => `
                    <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                        <span>${p.nombre} - $${p.precio} x ${p.cantidad}</span>
                        <div>
                            <button class="btn btn-secondary btn-sm me-1" onclick="cambiarCantidad(${i}, -1)">-</button>
                            <button class="btn btn-secondary btn-sm me-2" onclick="cambiarCantidad(${i}, 1)">+</button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarProducto(${i})">Eliminar</button>
                        </div>
                    </div>
                `).join("")
            }
        </div>
        ${carrito.length > 0 ? `
            <div class="mt-4">
                <h5 class="text-white">Total: $${carrito.reduce((t, p) => t + (p.precio * p.cantidad), 0)}</h5>

                <div class="mt-3">
                    <label class="text-white">Método de pago:</label>
                    <select id="metodoPago" class="form-select mt-1">
                        <option value="">Seleccione...</option>
                        <option value="Nequi">Nequi</option>
                        <option value="Efectivo">Efectivo</option>
                    </select>
                </div>

                <div id="campoCambio" class="mt-3" style="display: none;">
                    <label class="text-white">¿Con cuánto paga? (solo números):</label>
                    <input type="number" id="necesitaCambio" class="form-control mt-1" placeholder="Ejemplo: 50000" min="0">
                </div>

                <div class="mt-3">
                    <label class="text-white">Descripción o nota (opcional):</label>
                    <textarea id="descripcion" class="form-control mt-1" rows="2" placeholder="Ej: Sin cebolla, agregar servilletas..."></textarea>
                </div>

                <button class="btn btn-success mt-3 w-100" onclick="enviarPedido()">Enviar pedido</button>
            </div>
        ` : ""}
    `;

    // Detectar cambio de método de pago
    const metodoPagoSelect = document.getElementById("metodoPago");
    const campoCambio = document.getElementById("campoCambio");

    metodoPagoSelect?.addEventListener("change", () => {
        campoCambio.style.display = metodoPagoSelect.value === "Efectivo" ? "block" : "none";
    });
}

// Cambiar cantidad (+ o -)
function cambiarCantidad(index, cambio) {
    carrito[index].cantidad += cambio;
    if (carrito[index].cantidad <= 0) {
        carrito.splice(index, 1);
    }
    localStorage.setItem("carrito", JSON.stringify(carrito));
    mostrarCarrito();
}

// Eliminar producto del carrito
function eliminarProducto(index) {
    carrito.splice(index, 1);
    localStorage.setItem("carrito", JSON.stringify(carrito));
    mostrarCarrito();
}

// Enviar pedido al backend
async function enviarPedido() {
    const clienteData = JSON.parse(localStorage.getItem("cliente"));
    const metodoPago = document.getElementById("metodoPago").value;
    const necesitaCambio = document.getElementById("necesitaCambio")?.value || null;
    const descripcion = document.getElementById("descripcion").value.trim();

    if (!clienteData || !clienteData.id) {
        alert("Error: No se encontró el ID del cliente. Regístrate nuevamente.");
        return;
    }

    if (!metodoPago) {
        alert("Por favor selecciona un método de pago.");
        return;
    }

    const pedido = {
        cliente_id: clienteData.id,
        metodo_pago: metodoPago,
        necesita_cambio: metodoPago === "Efectivo" ? parseInt(necesitaCambio || 0) : 0,
        descripcion: descripcion || "",
        items: carrito.map(p => ({
            producto_id: p.id,
            nombre_producto: p.nombre,
            precio: p.precio,
            cantidad: p.cantidad
        }))
    };

    try {
        const response = await fetch("http://127.0.0.1:8000/pedidos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pedido)
        });

        if (response.ok) {
            const data = await response.json();
            const numeroPedido = data.id || data.numero_pedido || "N/A"; // ahora usa el ID autoincrementable

            localStorage.removeItem("carrito");
            localStorage.setItem("pedidoNumero", numeroPedido);

            // Redirigir según el método de pago
            if (metodoPago === "Efectivo") {
                window.location.href = "./efectivo.html";
            } else {
                window.location.href = "./nequi.html";
            }
        } else {
            const errorText = await response.text();
            console.error("Respuesta del servidor:", errorText);
            alert("Error al enviar el pedido ❌");
        }
    } catch (error) {
        console.error("Error al enviar el pedido:", error);
        alert("No se pudo conectar con el servidor.");
    }
}

// Mostrar carrito al cargar
mostrarCarrito();
