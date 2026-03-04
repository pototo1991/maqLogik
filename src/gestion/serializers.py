from rest_framework import serializers
from .models import Maquinaria, Checklist, GPSLog

class MaquinariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquinaria
        # Excluimos empresa explícitamente porque es manejado internamente
        exclude = ['empresa']

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        exclude = ['empresa', 'usuario']

class GPSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSLog
        exclude = ['empresa']
