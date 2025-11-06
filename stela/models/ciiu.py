#Clasificacion CIIU Rev 4
from django.db import models

class Ciiu(models.Model):

    codigo = models.CharField(max_length=10, primary_key=True)
    descripcion = models.CharField(max_length=255)
    nivel = models.IntegerField()
    padre = models.ForeignKey(
        'self',                    
        on_delete=models.CASCADE,  
        null=True,                 
        blank=True,                 
        related_name='hijos'        
    )

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"