from django.contrib.auth.models import AbstractUser
from django.db import models

# Heredar modelo User y agregar campos adicionales
class CustomUser(AbstractUser):
    telephone = models.CharField(max_length=9, blank=True, null=True)
    dui = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.username

# Registrar opciones de formulario
class OptionForm(models.Model):
    optionId = models.CharField(max_length=3, primary_key=True)
    description = models.CharField(max_length=50)
    formNumber = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.optionId} - {self.description}"

    class Meta:
        verbose_name = "Option Form"
        verbose_name_plural = "Option Forms"

# Modelo para asignar acceso de usuario a opciones de formulario
class UserAccess(models.Model):
    userId = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    optionId = models.ForeignKey(OptionForm, on_delete=models.CASCADE)
    # aun no esta creado companyId = models.ForeignKey('Company', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.userId.username} - {self.optionId.description}"

    class Meta:
        verbose_name = "User Access"
        verbose_name_plural = "User Accesses"
        unique_together = ('userId', 'optionId')
        # unique_together = ('userId', 'companyId') cuando se cree el modelo Company

    