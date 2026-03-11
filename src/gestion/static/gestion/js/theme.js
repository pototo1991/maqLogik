// theme.js - Manejo del Tema Claro/Oscuro

function initTheme() {
    // 1. Revisar si hay una preferencia guardada en localStorage
    const savedTheme = localStorage.getItem('maqlogik-theme');
    
    // 2. Si existe preferencia y es 'light', aplicar al HTML inmediatamente
    if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }
}

// Ejecutamos la función INMEDIATAMENTE al cargar este script
// (Se coloca en el <head> para que el HTML se dibuje ya con el color correcto)
initTheme();

// Función que será llamada por el botón en la Topbar
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const themeBtnIcon = document.getElementById('theme-toggle-icon');
    
    if (currentTheme === 'light') {
        // Volver a Oscuro (Eliminando el atributo se usan los valores por defecto de :root)
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('maqlogik-theme', 'dark');
        if(themeBtnIcon) themeBtnIcon.textContent = '☀️'; // Sol listo para ir a claro
    } else {
        // Cambiar a Claro
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('maqlogik-theme', 'light');
        if(themeBtnIcon) themeBtnIcon.textContent = '🌙'; // Luna lista para ir a oscuro
    }
}

// Inicializar el aspecto del botón una vez que el DOM cargue
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('maqlogik-theme');
    const themeBtnIcon = document.getElementById('theme-toggle-icon');
    
    if(themeBtnIcon) {
        if (savedTheme === 'light') {
            themeBtnIcon.textContent = '🌙'; 
        } else {
            themeBtnIcon.textContent = '☀️';
        }
    }
});

// =============================================
// DROPDOWN MENU AVATAR (Mi Cuenta)
// =============================================

function toggleAvatarMenu() {
    const dropdown = document.getElementById('avatarDropdown');
    if (dropdown) {
        dropdown.classList.toggle('open');
    }
}

// Cerrar el dropdown si el usuario hace click fuera de él
document.addEventListener('click', function(event) {
    const wrapper = document.getElementById('avatarWrapper');
    const dropdown = document.getElementById('avatarDropdown');
    if (wrapper && dropdown && !wrapper.contains(event.target)) {
        dropdown.classList.remove('open');
    }
});
