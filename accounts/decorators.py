from django.contrib import messages
from django.shortcuts import redirect
from accounts.models import UserAccess

def access_required(*option_ids, stay_on_page=False):
    """
    Verifica si el usuario tiene acceso a una o más opciones específicas.
    Si stay_on_page=True, bloquea acciones POST sin redirigir.
    Si stay_on_page=False, redirige a 'landing' si no tiene acceso.
    """

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Si no está autenticado, redirige al login
            if not user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para continuar.')
                return redirect('login')

            # Superusuarios tienen acceso total
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificar si tiene acceso a alguna de las opciones
            has_access = UserAccess.objects.filter(
                userId=user,
                optionId__optionId__in=option_ids
            ).exists()

            if not has_access:
                if stay_on_page:
                    if request.method == 'POST':
                        messages.error(request, 'No tienes permiso para realizar esta acción.')
                        return redirect(request.path)
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'No tienes permiso para acceder a esta vista.')
                    return redirect('landing')

            # Si tiene acceso, continúa
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

