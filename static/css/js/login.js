document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const showPasswordCheckbox = document.getElementById('showPassword');
    const passwordField = document.getElementById('password');
    let users = [];

    const fetchUsers = async () => {
        try {
            console.log('Cargando usuarios...');
            const response = await fetch('https://mana-51g3.onrender.com/usuarios'); 

            if (!response.ok) {
                throw new Error(`Error en la respuesta del servidor: ${response.status}`);
            }

            users = await response.json();  
            console.log('Usuarios cargados:', users);
        } catch (error) {
            console.error('Error al cargar los usuarios:', error);
        }
    };

    const limpiarDatos = () => {
        document.getElementById('username').value = "";  
        document.getElementById('password').value = "";  
    };
    showPasswordCheckbox.addEventListener('change', () => {
        if (showPasswordCheckbox.checked) {
            passwordField.type = 'text';
        } else {
            passwordField.type = 'password';
        }
    });

    fetchUsers();

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const usernameInput = document.getElementById('username').value.trim();
        const passwordInput = document.getElementById('password').value.trim();

        const userFound = users.find(user => user.usuario === usernameInput && user.contraseña === passwordInput);

        if (userFound) {
            console.log("Usuario encontrado:", userFound);
            localStorage.setItem("ingreso", JSON.stringify({ nombre: userFound.usuario }));
            
            
            window.location.href = './html/bienvenido.html';  

        } else {
            alert('Usuario o contraseña incorrectos');  
            console.log("No se encontró el usuario");
        }

        limpiarDatos(); 
    });
});
