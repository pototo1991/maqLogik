import time
import random
from django.core.management.base import BaseCommand
from gestion.models import Empresa, Maquinaria, GPSLog
from decimal import Decimal

class Command(BaseCommand):
    help = 'Inyecta datos falsos de GPS continuamente en la DB para una empresa y sus máquinas activas.'

    def handle(self, *args, **options):
        # Tomar la primera empresa existente
        empresa = Empresa.objects.first()
        if not empresa:
            self.stdout.write(self.style.ERROR('Debes crear al menos una Empresa primero.'))
            return

        maquinas = Maquinaria.objects.filter(empresa=empresa)
        if not maquinas.exists():
            self.stdout.write(self.style.ERROR('Debes crear al menos una Máquina para la primera empresa.'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'Iniciando tracking falso para empresa: {empresa.nombre_fantasia}'))
        
        # Puntos iniciales base para cada máquina en Santiago de Chile
        posiciones = {}
        for m in maquinas:
            posiciones[m.id] = {
                'lat': -33.4489 + random.uniform(-0.01, 0.01),
                'lng': -70.6693 + random.uniform(-0.01, 0.01),
                'velocidad': random.uniform(10.0, 60.0)
            }
            
        try:
            while True:
                for m in maquinas:
                    # Mover el punto un poquito cada vez
                    pos = posiciones[m.id]
                    nueva_lat = pos['lat'] + random.uniform(-0.0005, 0.0005)
                    nueva_lng = pos['lng'] + random.uniform(-0.0005, 0.0005)
                    nueva_velocidad = random.uniform(5.0, 65.0)
                    
                    pos['lat'] = nueva_lat
                    pos['lng'] = nueva_lng
                    pos['velocidad'] = nueva_velocidad
                    
                    # Registrar un nuevo Log
                    GPSLog.objects.create(
                        maquina=m,
                        empresa=empresa,
                        latitud=Decimal(str(round(nueva_lat, 6))),
                        longitud=Decimal(str(round(nueva_lng, 6))),
                        velocidad=nueva_velocidad
                    )
                    
                    self.stdout.write(f'✅ Guardado GPSLog {m.id_interno}: {nueva_lat}, {nueva_lng} ({nueva_velocidad:.1f} km/h)')
                
                # Pausar 5 segundos antes del siguiente pulso
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nTracking de simulación detenido por el usuario.'))
