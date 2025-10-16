from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model
import re

User = get_user_model()

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        context = {'data': request.POST}

        # mascara de tel ####-####
        if not re.match(r'^\d{4}-\d{4}$', phone):
            messages.error(request, 'El número de teléfono debe tener el formato ####-####')
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

        # validar que solo exista un usuario y correo 
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return render(request, 'registration/register.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return render(request, 'registration/register.html', context)

        # crear usuario
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            telephone=phone
        )
        messages.success(request, 'Usuario registrado correctamente, inicie sesión con sus credenciales.')
        return redirect('login')

    return render(request, 'registration/register.html')
