from stela.models.empresa import Empresa


def empresas_usuario(request):
    """
    Context processor para agregar empresas del usuario actual a todos los templates.
    """
    if request.user.is_authenticated:
        empresas = Empresa.objects.filter(usuario=request.user).order_by('razon_social')
        return {
            'empresas_usuario': empresas,
            'empresas_count': empresas.count()
        }
    return {
        'empresas_usuario': [],
        'empresas_count': 0
    }

