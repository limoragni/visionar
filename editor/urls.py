from django.conf.urls import patterns, url

from editor import views

urlpatterns = patterns('',
    url(r'^uploadImage/$', views.uploadImage, name='uploadImage'),
    url(r'^deleteMedia/$', views.deleteMedia, name='deleteMedia'),
    url(r'^save/$', views.saveProject, name='saveProject'),
    url(r'^saveTitle/$', views.saveTitle, name='saveTitle'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^render/$', views.renderProject, name='renderProject'),
    url(r'^renderDone/$', views.renderDone, name='renderDone'),
    url(r'^getPreview/$', views.getPreview, name='getPreview'),
    url(r'^checkout/(?P<urlhash>\w+)/$', views.checkout, name='checkout'),
    url(r'^video/(?P<urlhash>\w+)/$', views.video, name='video'),
    url(r'^(?P<urlhash>\w+)/$', views.get, name='get'),
    url(r'^add/(?P<user>\w+)/(?P<template>\w+)/$', views.add, name='add'),
    #url(r'^render/$', views.render, name='render'),
   	url(r'^$', views.select_template, name='select_template'),
)
