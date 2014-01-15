# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template  import RequestContext
from django.contrib.auth.models import User
from .models import External, Plan, Datos_Facturacion, Pedido
from editor.models import Project, Media, Mediatype, RenderState
from django.core.context_processors import csrf
from visionar.utils import validation
import requests

def loginview(request):
    if request.user.is_authenticated():
        return redirect('/users/profile')
    else:
        return render(request, 'users/login.html', {'failed': False})
    
def auth_and_login(request, onsuccess='/create', onfail="/users/login/"):
    user = authenticate(username=request.POST['username'], password=request.POST['password'])
    if user is not None:
        login(request, user)
        return redirect(onsuccess)
    else:
        #return redirect(onfail)
        return render(request, 'users/login.html', {"failed": True}) 

def recover(request):
    return render(request, 'users/recover.html')

def create_user(username, email, password, first_name, last_name, company, phone):
	user = User(username=username, email=email, first_name=first_name, last_name=last_name)
	user.set_password(password)
	user.save()
	external = External(user=user ,company=company, phone=phone)
	external.save()
	return user

def user_exists(username):
    user_count = User.objects.filter(username=username).count()
    if user_count == 0:
        return False
    return True

def email_exists(email):
    user_count = User.objects.filter(email=email).count()
    if user_count == 0:
        return False
    return True

def signup(request):
    post = request.POST
    val = validate(post)
    if val == True:
        user = create_user(username=post['username'], email=post['email'], password=post['password'], first_name = post['first_name'], last_name = post['last_name'], company = post['company'], phone=post['phone'])
        return auth_and_login(request)
    else:
        return render(request, 'users/login.html', {"messages":val, "fields": request.POST})
    	

def validate(data):
    messages = {}
    if not user_exists(data['username']):
        if not validation.lengthValidation(data['username'], 4, 13):
            messages["username"] = u"El nombre debe tener un mínimo de 4 caractéres y un máximo de 13"
        if not validation.lengthValidation(data['password'], 4, 20):
            messages["password"] = u"El password debe tener un mínimo de 6 caractéres y un máximo de 20"
        if not validation.lengthValidation(data['first_name'], 3, 30):
            messages["first_name"] = u"El nombre debe tener un mínimo de 3 caractéres"
        if not validation.lengthValidation(data['last_name'], 3, 50):
            messages["last_name"] = u"El apellido debe tener un mínimo de 3 caractéres"
        if not validation.lengthValidation(data['company'], 3, 50):
            messages["company"] = u"La empresa debe contener un mínimo de 3 caractéres"
        if not validation.lengthValidation(data['phone'], 6, 20): 
            messages["phone"] = u"El número debe contener un mínimo de 6 caractéres"
        if not validation.is_number(data['phone']):
            messages["phone"] = u"El teléfono debe contener solamente números"
        if not validation.mailValidation(data['email']):
            messages["email"] = u"Ingrese un email válido"
        if email_exists(data['email']):
            messages["email"] = u"Ya existe una cuenta con este email asociado"
    else:
        messages["username"] = u"Usuario no disponible"
    if len(messages) == 0:
        return True
    else:
        return messages       
    

def logoutview(request):
    logout(request)
    return redirect("/users/login/")

def updateUser(request):
    user = User.objects.get(username=request.user)
    external = External.objects.get(user=user)
    user_dict = {
        "first_name":request.POST["first_name"],
        "last_name":request.POST["last_name"],
    }
    external_dict = {
        "company":request.POST["company"],
        "phone":request.POST["phone"],
    }
    
    user.__dict__.update(user_dict)
    external.__dict__.update(external_dict)
    user.save()
    external.save()
    return redirect("/users/profile/")

@login_required(login_url='/users/login/')
def profile(request):
    user = User.objects.get(username=request.user)
    return render(request, "users/profile.html", {"user":user})

@login_required(login_url='/users/login/')
def video(request):
    finished = Project.objects.filter(user=request.user).filter(state__in=[RenderState.objects.get(name="FINISHED"), RenderState.objects.get(name="PENDING")])
    unfinished = Project.objects.filter(user=request.user).filter(state=RenderState.objects.get(name="NONE"))
    published =  Project.objects.filter(user=request.user).filter(state=RenderState.objects.get(name="PUBLISHED"))

    pagination = {
        'finished': int((finished.count() / 3) // 1),
        'unfinished': int((unfinished.count() / 3) // 1)
    }
    return render(request, "users/video.html", {"finished": finished, "unfinished": unfinished, 'published':published, 'pagination': pagination})

@login_required(login_url='/users/login/')
def publicar(request, plan_id, project):
    plan = Plan.objects.get(id=plan_id)
    if Datos_Facturacion.objects.filter(user=request.user):
        datos = Datos_Facturacion.objects.get(user=request.user)
    else:
        datos = None
    return render(request, "users/publicar.html", {"plan": plan, "datos": datos, "project": project})

def pedido(request):
    project = Project.objects.get(urlhash=request.POST["project"])
    project.state = RenderState.objects.get(name="PUBLISHED")
    project.save()
    
    if Datos_Facturacion.objects.filter(user=request.user):
        datos = Datos_Facturacion.objects.get(user=request.user)
        dict_data = {
            "tipo_iva" : request.POST["tipo_iva"],
            "cuit" : request.POST["cuit"], 
            "razon_social" : request.POST["razon_social"], 
            "nombre_fantasia" : "",  
            "direccion" : request.POST["direccion"], 
            "localidad" : request.POST["localidad"], 
            "provincia" : request.POST["provincia"], 
            "pais": request.POST["pais"], 
            "codigo_iva" : ""
        } 
        datos.__dict__.update(dict_data)
        datos.save()
    else:
        datos = Datos_Facturacion(
            user= request.user,
            tipo_iva= request.POST["tipo_iva"],
            cuit= request.POST["cuit"], 
            razon_social= request.POST["razon_social"], 
            nombre_fantasia= "",  
            direccion= request.POST["direccion"], 
            localidad= request.POST["localidad"], 
            provincia= request.POST["provincia"], 
            pais= request.POST["pais"], 
            codigo_iva= ""
        )
        datos.save()
    
    pedido = Pedido(user=request.user, project=project, plan=Plan.objects.get(id=request.POST["plan"]), cantidad=1, tipo_pago=request.POST["forma-pago"], payment_state = "Pendiente")        
    pedido.save()
    return render(request, "users/pedido.html", {"pedido": pedido, "datos": datos})

def facturar(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    user = pedido.user
    plan = pedido.plan
    datos_facturacion = Datos_Facturacion.objects.get(user=user)
    link = "/media/facturas/pdf.pdf" #TODO: link a pdf de factura
    return render(request, "users/factura.html", {"link": link})
