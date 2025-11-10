from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

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
    userId = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    optionId = models.ForeignKey(OptionForm, on_delete=models.SET_NULL, null=True)
    companyId = models.ForeignKey('stela.Empresa', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        user = self.userId.username if self.userId else "Sin usuario"
        option = self.optionId.description if self.optionId else "Sin opción"
        empresa = self.companyId.razon_social if self.companyId else "Sin empresa"
        return f"{user} - {option} - {empresa}"

    def delete(self, *args, **kwargs):
        if self.userId and self.optionId and self.companyId:
            raise ValidationError("No se puede borrar este acceso porque aún existen empresa, usuario y opción.")
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "User Access"
        verbose_name_plural = "User Accesses"
        unique_together = ('userId', 'optionId', 'companyId')


    