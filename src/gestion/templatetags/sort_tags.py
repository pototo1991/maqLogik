from django import template

register = template.Library()

@register.simple_tag
def sort_icon(field, current_sort, current_dir):
    """
    Devuelve un ícono visual (▲ o ▼) si el campo actual es el que está ordenado.
    """
    if field == current_sort:
        return ' ▲' if current_dir == 'asc' else ' ▼'
    return ''

@register.simple_tag(takes_context=True)
def sort_url(context, field, current_sort, current_dir):
    """
    Devuelve la query string para la URL invirtiendo la dirección
    si se hace click en la misma columna. Preserva el parámetro de
    búsqueda 'q' si existe.
    """
    if field == current_sort:
        next_dir = 'desc' if current_dir == 'asc' else 'asc'
    else:
        next_dir = 'asc'
        
    request = context.get('request')
    query_str = f"?sort={field}&dir={next_dir}"
    
    if request:
        q = request.GET.get('q')
        if q:
            import urllib.parse
            query_str += f"&q={urllib.parse.quote_plus(q)}"
            
    return query_str
