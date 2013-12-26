from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template  import RequestContext
from django.contrib.auth.models import User
from .models import External, Plan, Datos_Facturacion, Pedido
from editor.models import Project, Media, Mediatype, RenderState
from django.core.context_processors import csrf
import requests

def loginview(request):
    if request.user.is_authenticated():
        return redirect('/users/profile')
    else:
        return render(request, 'users/login.html')
    

def auth_and_login(request, onsuccess='/create', onfail="/users/login/"):
    user = authenticate(username=request.POST['username'], password=request.POST['password'])
    if user is not None:
        login(request, user)
        return redirect(onsuccess)
    else:
        return redirect(onfail)  

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

def signup(request):
    post = request.POST
    if not user_exists(post['username']): 
        user = create_user(username=post['username'], email=post['email'], password=post['password'], first_name = post['first_name'], last_name = post['last_name'], company = post['company'], phone=post['phone'])
    	return auth_and_login(request)
    else:
    	return redirect("/users/login/")

def logoutview(request):
    logout(request)
    return redirect("/users/login/")

@login_required(login_url='/users/login/')
def profile(request):
    return render(request, "users/profile.html")

@login_required(login_url='/users/login/')
def video(request):
    finished = Project.objects.filter(user=request.user).filter(state=RenderState.objects.get(name="FINISHED"))
    unfinished = Project.objects.filter(user=request.user).filter(state=RenderState.objects.get(name="NONE"))
   

    pagination = {
        'finished': int((finished.count() / 3) // 1),
        'unfinished': int((unfinished.count() / 3) // 1)
    }
    return render(request, "users/video.html", {"finished": finished, "unfinished": unfinished, 'pagination': pagination})

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
    if Datos_Facturacion.objects.filter(user=request.user):
        datos = Datos_Facturacion.objects.get(user=request.user)
        datos.tipo_iva = request.POST["tipo_iva"],
        datos.cuit = request.POST["cuit"], 
        datos.razon_social = request.POST["razon_social"], 
        datos.nombre_fantasia = "",  
        datos.direccion = str(request.POST["direccion"]), 
        datos.localidad = str(request.POST["localidad"]), 
        datos.provincia = str(request.POST["provincia"]), 
        datos.pais = str(request.POST["pais"]), 
        datos.codigo_iva = ""
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
    pedido = Pedido(user=request.user, project=project, plan=Plan.objects.get(id=request.POST["plan"]), cantidad=1, tipo_pago=request.POST["forma-pago"])        
    pedido.save()
    return render(request, "users/pedido.html", {"pedido": pedido, "datos": datos})

def facturar(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    user = pedido.user
    plan = pedido.plan
    datos_facturacion = Datos_Facturacion.objects.get(user=user)
    link = "/media/facturas/pdf.pdf" #TODO: link a pdf de factura
    return render(request, "users/factura.html", {"link": link})
