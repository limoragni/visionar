import socket
import ntpath
import json
from django.core.context_processors import csrf

from django.utils import simplejson
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response, redirect

from .response import JSONResponse, response_mimetype
from .models import Template, Project, Image, Text, Mediatype, Media

from base64 import b64decode
from django.core.files.base import ContentFile

import requests
import visionar.config.environment as env

import redis
import logging

logger = logging.getLogger(__name__)

@login_required(login_url='/users/login/')
def select_template(request):
    temp = Template.objects.all()
    return render(request, "editor/select_template.html", {"temp": temp})


@login_required(login_url='/users/login/')
def get(request, urlhash):
	if Project.objects.get(urlhash=urlhash):
		project = Project.objects.get(urlhash=urlhash)
		positions = json.dumps(project.positions)
		media_set = Media.objects.filter(project=project).filter(mediatype=Mediatype.objects.get(typename="Image"))
		media_sorted = sorted(media_set, key=lambda a: a.position)
		return render(request, "editor/project.html", {"project": project, "media": media_sorted})
	else:
		return redirect('/users/login/')
	

@login_required(login_url='/users/login/')
def add(request, user, template):
	if (str(user) ==str(request.user)) & Template.objects.filter(name=template).exists():
		user = User.objects.get(username=request.user)
		template = Template.objects.get(name=template)
		project = Project(user=user, template=template, istmp=False)
		project.save()
		return redirect('/project/' + project.urlhash)
	else:
		return redirect('/users/login/')

@login_required(login_url='/users/login/')
def checkout(request):
	return render(request, 'editor/checkout.html')

def saveProject(request):
	if (str(request.POST["user"]) ==str(request.user)) & Project.objects.filter(urlhash=request.POST["project"]).exists():
		project = Project.objects.get(urlhash=request.POST["project"])
		project.positions = request.POST["positions"]
		project.save()
		r = "El proyecto fue guardado con exito"
	else:
		r = "No se puede guardar"	
	
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

def renderProject(request):
	red = redis.StrictRedis(host='localhost', port=6379, db=0)
	red.delete(request.POST["project"])

	project = Project.objects.get(urlhash=str(request.POST["project"]));
	imgs = Media.objects.filter(project=project).filter(mediatype=Mediatype.objects.get(typename="Image"))
	imgs_sorted = sorted(imgs, key=lambda a: a.position)
	data = {
	    'media_data': [],
	    'media_url': str(project.getImagesPath()),
	    'code': str(project.urlhash), 
	}

	for i in imgs_sorted:
		data["media_data"].append(str(ntpath.basename(i.image.file.path)))
	
	headers = {'content-type': 'application/json'}
	try:
		r = requests.post(env.BLENDER_URL, data=json.dumps(data), headers=headers)
		message = r.json()
	except Exception as e:
		message = {'response':e}
	
	response = JSONResponse(message, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json' 
	return response  

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
			r = redis.StrictRedis(host='localhost', port=6379, db=0)
			r.set(request.POST["code"], request.POST["urls"])
			return HttpResponse("OKAA MAN")
	except Exception as e:
		logger.error(e)
		return HttpResponse(e)

def getPreview(request):
	r = redis.StrictRedis(host='localhost', port=6379, db=0)
	response = r.get(request.POST["project"])
	if not response:
		response = "PENDING"
	response = JSONResponse({'response': response}, mimetype=response_mimetype(request))
	response['Content-Disposition'] = 'inline; filename=files.json' 
	return response 
