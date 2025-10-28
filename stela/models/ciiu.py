#Clasificacion CIIU Rev 4
from django.db import models

class Ciuu(models.Model):

    codigo = models.CharField(max_length=10, primary_key=True)
    descripcion = models.CharField(max_length=255)
    nivel = models.IntegerField()
    padre = models.ForeignKey(
        'self',                     # 1. Apunta al mismo modelo (Ciuu)
        on_delete=models.CASCADE,  # 2. Qué hacer si se borra el padre
        null=True,                  # 3. Permite que el campo sea NULO en la BD
        blank=True,                 # 4. Permite que el campo esté vacío en forms
        related_name='hijos'        # 5. Nombre para la relación inversa
    )

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"