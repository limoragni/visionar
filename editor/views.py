# -*- coding: utf-8 -*-
import socket
import ntpath
import json
import redis
from django.core.context_processors import csrf

from django.utils import simplejson
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response, redirect

from .response import JSONResponse, response_mimetype
from .models import Template, Project, Image, Text, Mediatype, Media, RenderState, RenderType
from users.models import Plan, Pedido

from base64 import b64decode
from django.core.files.base import ContentFile

import requests
import visionar.config.environment as env

import redis
import logging

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

@login_required(login_url='/users/login/')
def select_template(request):
    temp = Template.objects.all()
    return render(request, "editor/select_template.html", {"temp": temp})


@login_required(login_url='/users/login/')
def get(request, urlhash):
	if Project.objects.get(urlhash=urlhash):
		project = Project.objects.get(urlhash=urlhash)
		if project.user == request.user:
			positions = json.dumps(project.positions)
			media_set = Media.objects.filter(project=project).filter(mediatype=Mediatype.objects.get(typename="Image"))
			media_sorted = sorted(media_set, key=lambda a: a.position)
			if project.texts:
				texts = json.loads(project.texts)
			else:
				texts = None
			return render(request, "editor/project.html", {"project": project, "media": media_sorted, "texts": texts})
		else:
			return redirect('/users/video/')
	else:
		return redirect('/users/login/')
	

@login_required(login_url='/users/login/')
def add(request, user, template):
	if (str(user) == str(request.user)) & Template.objects.filter(name=template).exists():
		user = User.objects.get(username=request.user)
		template = Template.objects.get(name=template)
		render_state = RenderState.objects.get(name="NONE")
		project = Project(user=user, template=template, state=render_state)
		project.save()
		return redirect('/project/' + project.urlhash)
	else:
		return redirect('/users/login/')

@login_required(login_url='/users/login/')
def delete(request):
	if Project.objects.get(urlhash=request.POST['urlhash']):
		project = Project.objects.get(urlhash=request.POST['urlhash'])
		project.delete()
		response = "PROJECT DELETED"
	else:
		response = "NOT FOUND"
	response = JSONResponse({'response': response}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json'
	return response


def saveProject(request):
	if (str(request.POST["user"]) == str(request.user)) & Project.objects.filter(urlhash=request.POST["project"]).exists():
		project = Project.objects.get(urlhash=request.POST["project"])
		if "images" in request.POST:
			project.positions = request.POST["images"]
		if "texts" in request.POST:
			project.texts = request.POST["texts"]
		project.save()
		r = "El proyecto fue guardado con exito"
	else:
		r = "No se puede guardar"	
	
	response = JSONResponse({'response': r}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json'
	return response

def saveTitle(request):
	if (str(request.POST["user"]) == str(request.user)) & Project.objects.filter(urlhash=request.POST["project"]).exists():
		project = Project.objects.get(urlhash=request.POST["project"])
		project.title = request.POST["title"]
		project.save()
		r = True
	else:
		r = False

	response = JSONResponse({'response': r}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json'
	return response

def updatePositions(project, id, delete=False):
	if project.positions:
		plist =  [ int(x) for x in json.loads(project.positions) ]
	else:
		plist = []
	
	if delete:
		plist.remove(int(id))
	else:
		plist.append(int(id))
	
	if plist:	
		project.positions = json.dumps(plist)
	else:
		project.positions = []
	
	project.save()

def uploadImage(request):
	project = Project.objects.get(urlhash=str(request.POST["project"]))
	mediatype = Mediatype.objects.get(typename="Image")
	img = Image(project= project, mediatype=mediatype)
              
	_, b64data = request.POST["data"].split(',')
	image_data = b64decode(b64data)
	img.file = ContentFile(image_data, request.POST["filename"])
	
	img.save()
	thumb_url = img.file['avatar'].url
	
	updatePositions(project, img.id)
	
	response = JSONResponse({'thumb': thumb_url, 'id': str(img.id)}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json'
	return response

def deleteMedia(request):
	media = Media.objects.get(id=int(request.POST["media"]))
	
	updatePositions(media.project, media.id, True)
	media.image.file.delete()
	media.delete()
	response = JSONResponse({'response': "DELETED"}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json'
	return response

#IN: Codigo del proyecto
#OUT: Datos para renderizar
def getRenderData(urlhash, render_type):
	project = Project.objects.get(urlhash=urlhash);
	imgs = Media.objects.filter(project = project).filter(mediatype=Mediatype.objects.get(typename="Image"))
	imgs_sorted = sorted(imgs, key=lambda a: a.position)
	if not project.texts:
		texts = ""
	else:
		texts = json.loads(project.texts)
	
	data = {
	    'media_data': [],
	    'texts': texts,
	    'media_url': str(project.getImagesPath()),
	    'code': str(project.urlhash),
	    'render_type': str(render_type),
	    'template': str(project.template.name)
    }

	for i in imgs_sorted:
		data["media_data"].append(str(ntpath.basename(i.image.file.path)))

	return data

def sendRenderData(data):
	headers = {'content-type': 'application/json'}
	try:
		r = requests.post(env.BLENDER_URL, data=json.dumps(data), headers=headers)
		message = r.json()
		if data['render_type'] == "FINAL":
			sendRenderNotification()
	except Exception as e:
		message = {'response':e}
	return message


def renderFinal(project):
	render_type = RenderType.objects.get(name="FINAL")
	data = getRenderData(project, render_type.name)
	message = sendRenderData(data)
	return message

def renderProject(request): #TODO: Agregar parametro QUALITY Cambiar nombre de funcion a renderPreview
	red = redis.StrictRedis(host='localhost', port=6379, db=0)
	red.delete(request.POST["project"])
	render_type = RenderType.objects.get(name="PREVIEW")
	data = getRenderData(request.POST["project"], render_type.name)
	message = sendRenderData(data)
	
	response = JSONResponse(message, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json' 
	return response  

@login_required(login_url='/users/login/')
def checkout(request, urlhash):
	if Project.objects.get(urlhash=str(urlhash)):
		project = Project.objects.get(urlhash=str(urlhash))
		renderFinal(str(urlhash))
		project.state = RenderState.objects.get(name="PENDING")
		project.urlrender = None
		project.save()
		return redirect('/project/video/' + urlhash)
		#return render(request, 'editor/checkout.html', {"project": project})
	else:	
		return render(request, 'editor/checkout.html', {"error": "Proyecto inexistente"})

def video(request, urlhash):
	project = Project.objects.get(urlhash=str(urlhash))
	pedidos = Pedido.objects.filter(project = project)
	plans = Plan.objects.all()
	if project.urlrender:
		urls = json.loads(project.urlrender)
	else:
		urls = None
	return render(request, 'editor/checkout.html', {"project": project, 'urls': urls, 'plans': plans, 'pedidos':pedidos})	

def sendToBlender(data):
	js = simplejson.dumps(data)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('127.0.0.1', 13373))
	s.send(js)
	result = json.loads(s.recv(1024))
	s.close()
	return result

def renderDone(request):
	try:
		if request.method == 'GET':
			c = {}
			c.update(csrf(request))
			return render_to_response('empty.html', c)
		elif request.method == 'POST':
			if str(request.POST["render_type"]) == str(RenderType.objects.get(name="FINAL").name):
				logger.error(type(request.POST["render_type"]))
				project = Project.objects.get(urlhash=request.POST["code"])
				project.state = RenderState.objects.get(name="FINISHED")
				project.urlrender = request.POST["urls"];
				project.save()
				sendRenderNotification(project.title, project.urlhash, project.user.username, project.user.email)
			else:
				r = redis.StrictRedis(host='localhost', port=6379, db=0)
				r.set(request.POST["code"], request.POST["urls"])
			return HttpResponse("")
	except Exception as e:
		logger.error(e)
		return HttpResponse(e)

def sendRenderNotification(title, key, username, email):
	sender = 'info@visionar.com.ar'
	receivers = [email]
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Confirmación de email"
	msg['From'] = sender
	msg['To'] = email

	s = smtplib.SMTP('localhost')
	url = env.HOST + "project/video/" + key + 

	text = "Su proyecto "+ title +" ha finalizado el render, dirigíte al siguiente link... " + url
	html = '''
	<html>
	  <head></head>
	  <body>
	       <h3>Render Finalizado</h3>
	       <p>Hola, <strong>''' + username + '''<strong></p>
	       <p>El render del proyecto '''+ title + '''a finalizado.</p>
	       <p>Dirigíte a <a href="''' + url + '''">este link</a> para verlo y realizar el pago.</p>
	  </body>
	</html>
	'''
	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')

	msg.attach(part1)
	msg.attach(part2)

	s.sendmail(sender, receivers, msg.as_string())

	s.quit()

def getPreview(request):
	r = redis.StrictRedis(host='localhost', port=6379, db=0)
	response = r.get(request.POST["project"])
	if not response:
		response = "PENDING"
	response = JSONResponse({'response': response}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json' 
	return response
