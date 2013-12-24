from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import External, Datos_Facturacion, Factura, Item_Factura, Pedido


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class ExternalInline(admin.StackedInline):
    model = External
    can_delete = False
    verbose_name_plural = 'external'

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (ExternalInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Datos_Facturacion)
admin.site.register(Factura)
admin.site.register(Item_Factura)
admin.site.register(Pedido)
