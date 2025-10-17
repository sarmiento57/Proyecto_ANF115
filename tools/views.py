from django.shortcuts import render
from accounts.decorators import access_required


# Create your views here.
@access_required('017') # con access requieremed verifica si tiene acceso a la vista
# @access_required('017', stay_on_page=True) # con stay on page hace que si no tiene acceso no se vaya a otra pagina
# solo se usara para botones como eliminar,editar y agregar
# ejemplo aun no implementado, 050 sera una opcion de editar, el usuario tiene acceso a la vista pero no al boton 
# cuando precione el boton en ves de redirigirlo a login se quedara en la misma pagina
# pero mostrara un mensaje de error que no tiene acceso
def tools(request):
    return render(request, "tools/tools.html")