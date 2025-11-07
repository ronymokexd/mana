document.addEventListener("DOMContentLoaded", cargarPedidos);

async function cargarPedidos() {
  try {
    const res = await fetch("https://mana-51g3.onrender.com/pedidos_enviados");
    if (!res.ok) throw new Error("Error al obtener los pedidos");
    const pedidos = await res.json();

    const tabla = document.getElementById("tablaPedidos");
    tabla.innerHTML = "";

    const ocultos = JSON.parse(localStorage.getItem("pedidosOcultos") || "[]");

    const grupos = {};
    pedidos.forEach(p => {
      const clave = `${p.cliente}||${p.numero}||${p.direccion}||${p.barrio}`;
      if (!grupos[clave]) grupos[clave] = [];
      grupos[clave].push(p);
    });

    const claves = Object.keys(grupos);
    if (claves.length === 0) {
      tabla.innerHTML = '<tr><td colspan="13">No hay pedidos registrados</td></tr>';
      return;
    }

    claves.forEach(clave => {
      const grupo = grupos[clave];
      const ultimo = grupo[grupo.length - 1];
      const ultimoId = Number(ultimo.id);

      if (ocultos.includes(ultimoId)) return;

      const productos = grupo
        .map(p => `${p.producto} (${p.categoria || "Sin categoría"}) x${p.cantidad} - $${Number(p.total).toLocaleString()}`)
        .join("<br>");

      const cantidades = grupo.reduce((s, p) => s + Number(p.cantidad), 0);
      const total = grupo.reduce((s, p) => s + Number(p.total), 0);

      const fila = document.createElement("tr");
      fila.dataset.ultimoId = ultimoId;
      fila.innerHTML = `
        <td>${ultimoId}</td>
        <td>${ultimo.cliente}</td>
        <td>${ultimo.numero}</td>
        <td>${ultimo.direccion}</td>
        <td>${ultimo.barrio}</td>
        <td>${productos}</td>
        <td>${cantidades}</td>
        <td>$${total.toLocaleString()}</td>
        <td>${ultimo.metodo_pago || ""}</td>
        <td>${ultimo.necesita_cambio || ""}</td>
        <td>${ultimo.descripcion || ""}</td>
        <td>${ultimo.fecha || ""}</td>
        <td>
          <button class="btn btn-danger btn-sm btn-quitar">❌ Quitar</button>
          <button class="btn btn-primary btn-sm btn-imprimir">🧾 Imprimir</button>
        </td>
      `;
      tabla.appendChild(fila);

      fila.querySelector(".btn-quitar").addEventListener("click", () => {
        ocultarYGuardar(ultimoId, fila);
      });

      fila.querySelector(".btn-imprimir").addEventListener("click", () => {
        const datosFactura = {
          id: ultimoId,
          cliente: ultimo.cliente,
          numero: ultimo.numero,
          direccion: ultimo.direccion,
          barrio: ultimo.barrio,
          productos: grupo.map(p => ({ nombre: p.producto, categoria: p.categoria, cantidad: p.cantidad, total: p.total })),
          total: total,
          metodo_pago: ultimo.metodo_pago,
          necesita_cambio: ultimo.necesita_cambio,
          descripcion: ultimo.descripcion,
          fecha: ultimo.fecha
        };
        imprimirFactura(datosFactura);
      });
    });
  } catch (err) {
    console.error(err);
    const tabla = document.getElementById("tablaPedidos");
    if (tabla) tabla.innerHTML = '<tr><td colspan="13">Error al cargar los pedidos.</td></tr>';
  }
}

function ocultarYGuardar(id, fila) {
  fila.remove();
  const ocultos = JSON.parse(localStorage.getItem("pedidosOcultos") || "[]");
  if (!ocultos.includes(id)) {
    ocultos.push(id);
    localStorage.setItem("pedidosOcultos", JSON.stringify(ocultos));
  }
}

function imprimirFactura(datos) {
  const productosHtml = datos.productos
    .map(p => `${p.nombre} (${p.categoria || "Sin categoría"}) x${p.cantidad} - $${Number(p.total).toLocaleString()}`)
    .join("<br>");

  const vent = window.open("", "_blank");
  vent.document.write(`
    <html>
      <head>
        <title>Factura #${datos.id}</title>
        <style>
          body { font-family: monospace; font-size: 14px; width: 350px; margin: 0 auto; text-align: center; }
          .logo { width: 120px; margin: 0 auto 10px; display: block; }
          .datos { text-align: left; margin: 10px 0; font-size: 14px; }
          .linea { border-top: 1px dashed #000; margin: 10px 0; }
          table { width: 100%; font-size: 14px; margin-top: 6px; }
          td { vertical-align: top; padding: 4px 0; }
          .total { font-weight: bold; font-size: 16px; text-align: right; }
          .gracias { margin-top: 10px; font-size: 16px; font-weight: bold; }
        </style>
      </head>
      <body>
        <img src="https://github.com/ronymokexd/mana-imagenes/blob/main/mana.png?raw=true" class="logo">
        <div><strong>*** MANA ***</strong></div>
        <div class="datos">
          <div>Factura #: ${datos.id}</div>
          <div>Cliente: ${datos.cliente}</div>
          <div>Tel: ${datos.numero}</div>
          <div>Dirección: ${datos.direccion}</div>
          <div>Barrio: ${datos.barrio}</div>
        </div>
        <div class="linea"></div>
        <div style="text-align:left; font-size:14px;">
          ${productosHtml}
        </div>
        <div class="linea"></div>
        <div class="total">Total: $${Number(datos.total).toLocaleString()}</div>
        <div class="datos">
          Método de pago: ${datos.metodo_pago || ''}<br>
          ¿Necesita cambio?: ${datos.necesita_cambio || ''}
        </div>
        <div class="linea"></div>
        <div>Fecha: ${datos.fecha || ''}</div>
        <div class="gracias">¡Gracias por tu compra! 🥳</div>
        <script>window.print();</script>
      </body>
    </html>
  `);
  vent.document.close();
}
