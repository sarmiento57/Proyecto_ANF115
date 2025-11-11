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


def company_context(request):
    """
    Añade la lista de empresas del usuario y la empresa activa
    al contexto de todas las plantillas.
    """
    if not request.user.is_authenticated:
        return {}

    # 1. Obtener todas las empresas del usuario
    user_companies = Empresa.objects.filter(usuario=request.user).distinct().order_by('razon_social')

    # 2. Obtener el NIT activo de la sesión
    active_nit = request.session.get('active_company_nit')

    # 3. Si no hay NIT en sesión, pero el usuario tiene empresas,
    #    selecciona la primera por defecto y guárdala.
    if not active_nit and user_companies.exists():
        active_nit = user_companies.first().nit
        request.session['active_company_nit'] = active_nit

    return {
        'USER_COMPANIES': user_companies,  # Tu bucle for usará esto
        'active_company_nit': active_nit  # Lo usaremos para resaltar
    }

