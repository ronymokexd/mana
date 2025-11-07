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
        const response = await fetch("https://mana-51g3.onrender.com/pedidos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pedido)
        });

        const data = await response.json();

        if (response.ok) {
            const numeroPedido = data.id || data.numero_pedido || "N/A";

            localStorage.removeItem("carrito");
            localStorage.setItem("pedidoNumero", numeroPedido);

            if (metodoPago === "Efectivo") {
                window.location.href = "./efectivo.html";
            } else {
                window.location.href = "./nequi.html";
            }
        } else {
            console.error("Respuesta del servidor:", data);
            alert("Error al enviar el pedido ❌");
        }
    } catch (error) {
        console.error("Error al enviar el pedido:", error);
        alert("No se pudo conectar con el servidor.");
    }
}
