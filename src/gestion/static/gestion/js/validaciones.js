/**
 * validaciones.js
 * Script global para mejorar la experiencia de usuario (UX) en los formularios 
 * aplicando formateo de datos en tiempo real.
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ------------------------------------------------------------------------
    // 1. Formateo de RUT Chileno (Ej: 12.345.678-9)
    // ------------------------------------------------------------------------
    const rutInputs = document.querySelectorAll('input[name*="rut"]');
    
    rutInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let valor = e.target.value;
            
            // Limpiar todo lo que no sea número o la letra K
            valor = valor.replace(/[^0-9kK]/g, '');
            
            if (valor.length > 0) {
                // Separar cuerpo (números) del dígito verificador
                const cuerpo = valor.slice(0, -1);
                const dv = valor.slice(-1).toUpperCase();
                
                // Formatear cuerpo con puntos cada 3 dígitos
                let cuerpoFormat = '';
                for (let i = cuerpo.length - 1, j = 1; i >= 0; i--, j++) {
                    cuerpoFormat = cuerpo.charAt(i) + cuerpoFormat;
                    if (j % 3 === 0 && i !== 0) {
                        cuerpoFormat = '.' + cuerpoFormat;
                    }
                }
                
                // Solo si el usuario digitó más de 1 caracter procedemos a mostrar el guión
                if (valor.length > 1) {
                    e.target.value = cuerpoFormat + '-' + dv;
                } else {
                    e.target.value = valor;
                }
            }
        });
    });

    // ------------------------------------------------------------------------
    // 2. Formateo de Patente de Vehículo/Máquina
    // ------------------------------------------------------------------------
    const patenteInputs = document.querySelectorAll('input[name*="patente"]');
    
    patenteInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let valor = e.target.value;
            
            // Forzar mayúsculas
            valor = valor.toUpperCase();
            
            // Eliminar espacios y guiones ingresados accidentalmente
            valor = valor.replace(/[\s-]/g, '');
            
            // Truncar a máximo 6 caracteres alfanuméricos
            if (valor.length > 6) {
                valor = valor.substring(0, 6);
            }
            
            e.target.value = valor;
        });
    });

    // ------------------------------------------------------------------------
    // 3. Restricciones Teléfono / Celular
    // ------------------------------------------------------------------------
    // Busca los campos que se llamen teléfono en cualquier formulario
    const phoneInputs = document.querySelectorAll('input[name*="telefono"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let valor = e.target.value;
            
            // Permitir solo números y el símbolo '+' al inicio
            valor = valor.replace(/(?!^\+)[^\d]/g, '');
            
            e.target.value = valor;
        });
    });

    // ------------------------------------------------------------------------
    // 4. Prevención de Doble-Click (Submit Duplicado)
    // ------------------------------------------------------------------------
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Buscar si existe un botón primario tipo Neon o Normal de Guardar
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (submitBtn && !submitBtn.classList.contains('disabled')) {
                // Cambiar el texto a enviando... y bloquearlo para evitar doble registro
                const originalText = submitBtn.textContent;
                submitBtn.innerHTML = '⏱️ Procesando...';
                submitBtn.classList.add('disabled');
                submitBtn.style.pointerEvents = 'none'; // Deshabilitar clicks a nivel CSS
                
                // Si el backend lanza error y el usuario presiona "Back", reactivamos el botón tras 4 segundos
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.classList.remove('disabled');
                    submitBtn.style.pointerEvents = 'auto';
                }, 4000);
            }
        });
    });

});
