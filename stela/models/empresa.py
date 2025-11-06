#Clase Empresa
from django.db import models
from .ciiu import Ciiu
# importar la de customuser para relacionar empresa con usuario
from django.contrib.auth import get_user_model
User = get_user_model()

class Empresa(models.Model):

    nit = models.CharField(max_length = 14, primary_key=True)

    #Clasificacion CIIU Rev 4
    idCiiu= models.ForeignKey(
        Ciiu, 
        on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE, related_name='empresas'
    )
    nrc = models.CharField(max_length = 8, unique=True)
    razon_social = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.razon_social} (NIT: {self.nit})"
    
    
    