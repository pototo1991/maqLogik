document.addEventListener("DOMContentLoaded", function() {
    // Inicializar animaciones de scroll
    if (typeof AOS !== 'undefined') {
        AOS.init({
            once: true, // animar solo la primera vez que se scrollea
            offset: 50, // offset (in px) from the original trigger point
        });
    }
});
