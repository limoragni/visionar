from django.conf.urls import patterns, url

from users import views

urlpatterns = patterns('',
    #url(r'^(?P<user>\w+)/(?P<session>\d{1,6})/$', views.session, name='session'),
    #url(r'^upload/$', views.upload, name='upload'),
    url(r'^video/$', views.video, name='video'),
    url(r'^publicar/(?P<plan_id>\w+)/(?P<project>\w+)$', views.publicar, name='publicar'),
    url(r'^pedido/$', views.pedido, name='pedido'),
    url(r'^facturar/(?P<pedido_id>\w+)/$', views.facturar, name='facturar'),
    url(r'^profile/$', views.profile, name='profile'),
   	url(r'^login/', views.loginview, name='login'),
   	url(r'^auth/', views.auth_and_login, name='login'),
    url(r'^recover/', views.recover, name='recover'),
    url(r'^recover_pass/(?P<username>\w+)/(?P<key>.*)', views.recover_pass, name='recover_pass'),
    url(r'^recover_pass/', views.recover_pass, name='recoverPassPost'),
    url(r'^logout/$', views.logoutview, name='logout'),
   	url(r'^signup/', views.signup, name='signup'),
    url(r'^validate/(?P<user>\w+)/(?P<key>.*)$', views.email_confirmation, name='validate'),
    url(r'^updateUser/', views.updateUser, name='updateUser'),
    url(r'^$', views.loginview, name='loginBlank'),
)