from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'visionar.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    #url(r'^socket\.io/', 'editor.views.socketio', name='socketio'),
    url(r'^$', TemplateView.as_view(template_name='home.html', get_context_data=lambda: {"isHome": True})),
    url(r'^prices/$', TemplateView.as_view(template_name='prices.html')),
    url(r'^users/', include('users.urls')),
    url(r'^create/$', include('editor.urls')),
    url(r'^project/', include('editor.urls')),
    url(r'^admin/', include(admin.site.urls)),
    
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
