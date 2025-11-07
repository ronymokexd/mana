let datosUsuario = JSON.parse(localStorage.getItem("ingreso"));


if (datosUsuario && datosUsuario.nombre) {
    document.getElementById("resultado").innerHTML = "Bienvenida " + datosUsuario.nombre; // Mostrar el nombre del usuario
} else {
    document.getElementById("resultado").innerHTML = "Usuario no encontrado."; // Manejo de caso si no hay usuario
}
