from django.contrib import messages
from django.shortcuts import redirect, render
from accounts.models import UserAccess

def access_required(option_id, stay_on_page=False):
    
    # decorador se encargará de verificar si el usuario tiene acceso a la opción dada.
    # si stay_on_page es True, en caso de no tener acceso, recarga la misma vista en lugar de redirigir.
    
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user = request.user

            # si no esta logueado lo manda al login
            if not user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para continuar.')
                return redirect('login')

            # si es superuser tiene acceso a todo el sistema
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # si no tiene acceso a la opcion o a la vista
            if not UserAccess.objects.filter(userId=user, optionId__optionId=option_id).exists():
                messages.error(request, 'No tienes permiso para acceder a esta vista.')

                # esto hace que se quede en la misma pagina solo si stay_on_page es True
                if stay_on_page:
                    messages.error(request, 'No tienes permiso para realizar esta acción.')
                    return view_func(request, *args, **kwargs)
                
                # si stay_on_page es False lo manda al login
                return redirect('login')

            # si tiene acceso continua
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

