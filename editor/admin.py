from django.contrib import admin
from .models import Template, Tag, Mediatype

admin.site.register(Template)
admin.site.register(Tag)
admin.site.register(Mediatype)