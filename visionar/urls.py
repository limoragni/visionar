from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'visionar.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    #url(r'^socket\.io/', 'editor.views.socketio', name='socketio'),
    url(r'^users/', include('users.urls')),
    url(r'^create/$', include('editor.urls')),
    url(r'^project/', include('editor.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include('users.urls')),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

