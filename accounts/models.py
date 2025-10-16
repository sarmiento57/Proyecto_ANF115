from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    telephone = models.CharField(max_length=9, blank=True, null=True)
    dui = models.CharField(max_length=10, blank=True, null=True)
