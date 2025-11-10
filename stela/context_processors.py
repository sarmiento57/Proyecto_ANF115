from .models import Empresa
def user_data(request):
    user_name = None
    user_companies = []

    if request.user.is_authenticated:
        user = request.user
        user_name = user.username
        user_companies = user.empresas.all()

    return {
        'CURRENT_USER_NAME': user_name,
        'USER_COMPANIES': user_companies,
    }
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

