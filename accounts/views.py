from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import PerfilEditForm
import re
from .decorators import access_required

User = get_user_model()

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        dui = request.POST.get('dui', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        context = {'data': request.POST}

        # validar que todos los campos estén llenos
        if not all([first_name, last_name, email, dui, phone, username, password, password2]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'registration/register.html', context)


        # mascara de tel ####-####
        if not re.match(r'^\d{4}-\d{4}$', phone):
            messages.error(request, 'El número de teléfono debe tener el formato ####-####')
            return render(request, 'registration/register.html', context)
        
        # mascara de dui #########-#
        if not re.match(r'^\d{8}-\d$', dui):
            messages.error(request, 'El DUI debe tener el formato #########-#')
            return render(request, 'registration/register.html', context)

        # nombres solo con letras
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', first_name) or not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', last_name):
            messages.error(request, 'Los nombres y apellidos solo deben tener letras')
            return render(request, 'registration/register.html', context)

        # validar contraseñas
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'registration/register.html', context)

        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'registration/register.html', context)

        # validar que solo exista un usuario y correo y dui
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return render(request, 'registration/register.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return render(request, 'registration/register.html', context)
        
        if User.objects.filter(dui=dui).exists():
            messages.error(request, 'El DUI ya está registrado')
            return render(request, 'registration/register.html', context)

        # crear usuario
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            dui=dui,
            first_name=first_name,
            last_name=last_name,
            telephone=phone
        )
        messages.success(request, 'Usuario registrado correctamente, inicie sesión con sus credenciales.')
        return redirect('login')

    return render(request, 'registration/register.html')


@access_required('004')
def perfil_view(request):
    """
    Vista para mostrar el perfil del usuario actualmente logueado.
    Solo muestra su propia información.
    """
    user = request.user
    context = {
        'user': user,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'telephone': user.telephone,
        'dui': user.dui,
    }
    return render(request, 'registration/perfil.html', context)


@access_required('043', stay_on_page=True)
def perfil_edit(request):
    """
    Vista para editar el perfil del usuario actualmente logueado.
    Solo permite editar: first_name, last_name, telephone, email
    NO permite cambiar: username, dui
    """
    user = request.user
    
    if request.method == 'POST':
        form = PerfilEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('perfil_view')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = PerfilEditForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'registration/perfil_edit.html', context)
