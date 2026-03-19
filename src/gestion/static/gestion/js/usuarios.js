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
        inputTelefono.addEventListener('focus', function() {
            if (this.value === '') this.value = '+56';
        });
        inputTelefono.addEventListener('input', function() {
            if (!this.value.startsWith('+56')) {
                this.value = '+56' + this.value.replace(/[^0-9]/g, '');
            }
        });
    }

    const inputRut = document.getElementById('id_rut');
    if (inputRut) {
        inputRut.addEventListener('blur', function() {
            let valor = this.value.replace(/\./g, '').replace(/-/g, '').toUpperCase().trim();
            if (!valor) return;
            if (valor.length < 2) return;
            
            let cuerpo = valor.slice(0, -1);
            let dv = valor.slice(-1);
            
            // Dar formato visual: 12.345.678-9
            this.value = cuerpo.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.') + '-' + dv;
            
            // --- Validación Matemática del Algoritmo Módulo 11 ---
            let suma = 0;
            let multiplo = 2;
            for (let i = 1; i <= cuerpo.length; i++) {
                let index = multiplo * valor.charAt(cuerpo.length - i);
                suma = suma + index;
                if (multiplo < 7) { multiplo = multiplo + 1; } else { multiplo = 2; }
            }
            let dvEsperado = 11 - (suma % 11);
            let dvNum = (dv == 'K') ? 10 : (dv == 0 ? 11 : parseInt(dv));
            
            if (dvEsperado != dvNum) {
                if (!(dvEsperado == 11 && dvNum == 0) && !(dvEsperado == 10 && dv == 'K')) {
                    this.parentElement.style.position = 'relative';
                    this.style.borderColor = '#ef4444';
                    this.style.boxShadow = '0 0 8px rgba(239, 68, 68, 0.6)';
                    alert('El RUT ingresado (' + this.value + ') no es válido matemáticamente. Por favor verifique el dígito verificador.');
                } else {
                    this.style.borderColor = '#10b981';
                    this.style.boxShadow = '0 0 8px rgba(16, 185, 129, 0.6)';
                }
            } else {
                this.style.borderColor = '#10b981';
                this.style.boxShadow = '0 0 8px rgba(16, 185, 129, 0.6)';
            }
        });
    }
});
