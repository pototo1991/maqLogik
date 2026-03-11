from django.shortcuts import render

def landing_page(request):
    """
    Landing Page Comercial de MaqLogik.
    Página pública para presentación del software SaaS.
    """
    return render(request, 'gestion/landing/index.html')
