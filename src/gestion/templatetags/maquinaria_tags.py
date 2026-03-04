from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def formatear_medida(valor, tipo_medida):
    """
    Recibe un número (ej. 2100.50) y un tipo ('HORAS' o 'KM').
    Retorna el número redondeado sin ceros decimales seguido de 
    su abreviatura final ('hrs' o 'km'). Ej: "2100 hrs"
    """
    if valor is None:
        return "0"

    # Convertir a flotante/entero para quitar decimales vacios o redondear
    try:
        numero = int(round(float(valor)))
    except (ValueError, TypeError):
        numero = 0

    if tipo_medida == 'HORAS':
        return f"{numero} hrs"
    elif tipo_medida == 'KM':
        return f"{numero} km"
    else:
        return str(numero)
