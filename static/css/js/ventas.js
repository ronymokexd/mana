async function cargarPedidos() {
  try {
    const response = await fetch("https://mana-51g3.onrender.com/pedidos_enviados");
    if (!response.ok) throw new Error("Error al obtener los pedidos");
    const pedidos = await response.json();

    // 👉 Ordenar por ID para que los nuevos aparezcan abajo
    pedidos.sort((a, b) => a.id - b.id);

    const tabla = document.getElementById("tablaPedidos");
    tabla.innerHTML = ""; // Limpiar tabla

    if (!pedidos || pedidos.length === 0) {
      tabla.innerHTML = '<tr><td colspan="14">No hay pedidos registrados</td></tr>';
      return;
    }

    pedidos.forEach(p => {
      const fila = document.createElement("tr");
      fila.innerHTML = `
        <td>${p.id}</td>
        <td>${p.cliente || "Sin nombre"}</td>
        <td>
          ${p.numero || "Sin número"}
          ${p.numero ? `<a href="https://wa.me/57${p.numero.replace(/\D/g,'')}" target="_blank" class="btn btn-success btn-sm ms-2">WhatsApp</a>` : ''}
        </td>
        <td>${p.direccion || "Sin dirección"}</td>
        <td>${p.barrio || "Sin barrio"}</td>
        <td>${p.producto || "Desconocido"}</td>
        <td>${p.categoria || "Sin categoría"}</td>
        <td>${p.cantidad || 0}</td>
        <td>$${p.total || 0}</td>
        <td>${p.metodo_pago || "No especificado"}</td>
        <td>${p.necesita_cambio ? p.necesita_cambio : "No"}</td>
        <td>${p.descripcion ? p.descripcion : ""}</td>
        <td>${p.fecha ? new Date(p.fecha).toLocaleString() : "Sin fecha"}</td>
      `;
      tabla.appendChild(fila);
    });
  } catch (error) {
    console.error("Error:", error);
    document.getElementById("tablaPedidos").innerHTML =
      '<tr><td colspan="14">Error al cargar los pedidos</td></tr>';
  }
}

// Cargar pedidos al abrir la página
window.onload = cargarPedidos;

// Reiniciar pedidos (vaciar tabla en BD y reiniciar ID)
async function reiniciarPedidos() {
  if (!confirm("¿Seguro que deseas reiniciar todos los pedidos?")) return;

  try {
    const response = await fetch("http://127.0.0.1:8000/reiniciar_pedidos", {
      method: "DELETE"
    });

    if (!response.ok) throw new Error("Error al reiniciar pedidos");

    alert("Pedidos reiniciados correctamente");
    cargarPedidos();
  } catch (error) {
    console.error("Error:", error);
    alert("Error al reiniciar los pedidos");
  }
}

// Descargar PDF con los pedidos actuales
async function descargarPDF() {
  try {
    const response = await fetch("http://127.0.0.1:8000/pedidos_enviados");
    if (!response.ok) throw new Error("Error al obtener los pedidos");
    const pedidos = await response.json();

    if (!pedidos.length) {
      alert("No hay pedidos para descargar.");
      return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const fechaActual = new Date().toLocaleString();
    
    doc.setFontSize(16);
    doc.text("Reporte de Pedidos", 14, 15);

    doc.setFontSize(10);
    doc.text(`Generado el: ${fechaActual}`, 150, 15);

    doc.autoTable({
      head: [
        ["ID", "Cliente", "Número", "Producto", "Cantidad", "Total", "Método Pago", "Cambio", "Fecha del Pedido"]
      ],
      body: pedidos
        .sort((a, b) => a.id - b.id)
        .map(p => [
          p.id,
          p.cliente || "Sin nombre",
          p.numero ? `+57${p.numero.replace(/\D/g,'')}` : "Sin número",
          p.producto || "Desconocido",
          p.cantidad || 0,
          `$${p.total || 0}`,
          p.metodo_pago || "No especificado",
          p.necesita_cambio ? p.necesita_cambio : "No",
          p.fecha ? new Date(p.fecha).toLocaleString() : "Sin fecha"
        ]),
      startY: 25
    });

    doc.save(`reporte_pedidos_${new Date().toISOString().split('T')[0]}.pdf`);
  } catch (error) {
    console.error("Error al generar PDF:", error);
    alert("Error al generar el PDF.");
  }
}

// Eventos para botones
document.getElementById("btnReiniciar").addEventListener("click", reiniciarPedidos);
document.getElementById("btnPDF").addEventListener("click", descargarPDF);
