from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OptionForm, UserAccess

# si el modelo ya esta registrado, lo desregistramos primero
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('dui', 'telephone',)}),
    )
    list_display = UserAdmin.list_display + ('dui', 'telephone',)


@admin.register(OptionForm)
class OptionFormAdmin(admin.ModelAdmin):
    list_display = ('optionId', 'description', 'formNumber')
    search_fields = ('optionId', 'description')
    ordering = ('optionId',)


@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
    list_display = ('userId', 'optionId')
    list_filter = ('userId', 'optionId')
    search_fields = ('userId__username', 'optionId__description')

