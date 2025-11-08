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