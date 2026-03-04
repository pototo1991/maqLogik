// =========================================================================
//   MaqLogik - Lógica JS del Módulo Usuarios
// =========================================================================

document.addEventListener('DOMContentLoaded', function() {
    const inputNombre = document.getElementById('id_nombre_completo');
    const inputUsuario = document.getElementById('id_username');
    const inputTelefono = document.getElementById('id_telefono');

    if (inputNombre && inputUsuario) {
        inputNombre.addEventListener('input', function() {
            // Pasamos a minúsculas, quitamos tildes
            const valorLimpio = this.value.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            // Reemplazar espacios por guiones bajos y eliminar lo que no sea alfanumérico o guion bajo
            const usernameGenerado = valorLimpio.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
            inputUsuario.value = usernameGenerado;
        });
    }

    if (inputTelefono) {
        // Asegurar que siempre empiece con +56 al hacer focus/blur si está vacío
        inputTelefono.addEventListener('focus', function() {
            if (this.value === '') {
                this.value = '+56';
            }
        });
        // Validar que el usuario no borre el +56
        inputTelefono.addEventListener('input', function() {
            if (!this.value.startsWith('+56')) {
                this.value = '+56' + this.value.replace(/[^0-9]/g, '');
            }
        });
    }
});
