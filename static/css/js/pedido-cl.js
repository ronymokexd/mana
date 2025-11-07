document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('clienteForm');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nombre = document.getElementById('nombre').value.trim();
        const numero = document.getElementById('numero').value.trim();
        const direccion = document.getElementById('direccion').value.trim();
        const barrio = document.getElementById('barrio').value.trim();

        if (!nombre || !numero || !direccion || !barrio) {
            alert("Por favor complete todos los campos.");
            return;
        }

        const clienteData = {
            nombre: nombre,
            numero: numero,
            direccion: direccion,
            barrio: barrio
        };

        try {
            const response = await fetch('http://127.0.0.1:8000/clientes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(clienteData)
            });

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            const data = await response.json();
            console.log("Cliente registrado:", data);

            // Guardar cliente en localStorage con su ID
            clienteData.id = data.id;
            localStorage.setItem("cliente", JSON.stringify(clienteData));

            alert("Datos registrados correctamente. Redirigiendo al menú...");
            window.location.href = "./menu-pd.html"; // cambia por tu menú real
        } catch (error) {
            console.error("Error al registrar el cliente:", error);
            alert("No se pudo registrar el cliente. Inténtelo nuevamente.");
        }
    });
});
