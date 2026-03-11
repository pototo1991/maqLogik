import logging
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from gestion.models import Maquinaria, Usuario

logger = logging.getLogger('gestion')

class Command(BaseCommand):
    help = 'Envía correos electrónicos a los Owners con alertas de mantenimientos próximos.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando escaneo de mantenimientos preventivos...")
        
        # Diccionario para agrupar máquinas en alerta por su Empresa
        # Formato: { empresa_obj: [ maquina1, maquina2 ... ] }
        alertas_por_empresa = {}
        
        # Evaluamos TODAS las máquinas activas
        maquinas = Maquinaria.objects.filter(empresa__activa=True, empresa__modulo_mantencion=True)
        
        contador_alertas = 0
        for m in maquinas:
            # Lógica: Mostrar alerta si el medidor actual está a <= 50 uds de la próxima mantención
            if m.valor_actual_medida is not None and m.proximo_mantenimiento is not None:
                diferencia = m.proximo_mantenimiento - m.valor_actual_medida
                if diferencia <= 50:
                    # Agrupar por empresa
                    if m.empresa not in alertas_por_empresa:
                        alertas_por_empresa[m.empresa] = []
                    alertas_por_empresa[m.empresa].append({
                        'maquina': m,
                        'faltan': diferencia
                    })
                    contador_alertas += 1

        if contador_alertas == 0:
            self.stdout.write(self.style.SUCCESS('No se detectaron máquinas en rango crítico (<=50). Fin del proceso.'))
            return

        # Para cada empresa con alertas, construimos un correo
        for empresa, lista_alertas in alertas_por_empresa.items():
            # Buscar correos destinatarios: El OWNER y CHIEF de la empresa
            destinatarios = Usuario.objects.filter(
                empresa=empresa, 
                rol__in=['OWNER', 'CHIEF'], 
                is_active=True
            ).values_list('email', flat=True)
            
            # Limpiamos nulos o vacíos
            lista_correos = [email for email in destinatarios if email]
            
            if not lista_correos:
                self.stdout.write(self.style.WARNING(f"Alerta omitida para {empresa.nombre_fantasia}: No hay Owners/Chiefs con correo configurado."))
                continue
                
            # Renderizamos la plantilla HTML del correo
            context = {
                'empresa': empresa,
                'alertas': lista_alertas
            }
            html_message = render_to_string('gestion/emails/alerta_mantenimiento.html', context)
            plain_message = strip_tags(html_message)
            
            asunto = f"🚨 Alertas de Mantenimiento Preventivo - {empresa.nombre_fantasia}"
            
            # Configurar Correo
            msg = EmailMultiAlternatives(
                subject=asunto,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=lista_correos
            )
            msg.attach_alternative(html_message, "text/html")
            
            try:
                # Disparo SMTP
                msg.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS(f"✅ Correo de alertas enviado con éxito a {empresa.nombre_fantasia} ({len(lista_correos)} destinatarios)."))
                logger.info(f"Cron Job SMTP Exitoso: {empresa.nombre_fantasia} - {len(lista_alertas)} máquinas reportadas.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Fallo de envío SMTP a {empresa.nombre_fantasia}. Error: {str(e)}"))
                logger.error(f"Falla crítica en envío de Correos (Cron): {str(e)}")
                
        self.stdout.write(self.style.SUCCESS("Proceso de recordatorios semanales finalizado."))
