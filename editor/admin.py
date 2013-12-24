from django.contrib import admin
from .models import Template, Tag, Mediatype, RenderState, RenderType, Project

admin.site.register(Template)
admin.site.register(Tag)
admin.site.register(Mediatype)
admin.site.register(RenderState)
admin.site.register(RenderType)
admin.site.register(Project)
