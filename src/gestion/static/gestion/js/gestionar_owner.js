// Asignar clases nativas del formulario a los input del SetPasswordForm creado por Django
document.addEventListener("DOMContentLoaded", function() {
    const inputs = document.querySelectorAll('.form-card input[type="password"]');
    inputs.forEach(input => {
        input.classList.add('form-input');
        input.style.width = '100%';
    });
});
