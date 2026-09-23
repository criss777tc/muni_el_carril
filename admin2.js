document.getElementById('login').addEventListener('submit', async (e) => {

    e.preventDefault();

    const usuario = document.getElementById('usuario').value;
    const password = document.getElementById('password').value;

    try {

        const res = await fetch('http://localhost:5000/api/login', {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                usuario: usuario,
                password: password
            })
        });

        const data = await res.json();

        if (res.ok) {

            localStorage.setItem('token', data.token);
            localStorage.setItem('usuario', data.usuario);

            alert('¡Hola Mundo! Login exitoso como: ' + data.usuario);

            window.location.href = 'adminmuni.html';

        } else {

            alert(data.error || 'Usuario o contraseña incorrectos');

        }

    } catch (error) {

        console.error(error);

        alert('No se pudo conectar con el servidor');
    }
});