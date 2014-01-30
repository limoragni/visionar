# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template  import RequestContext
from django.contrib.auth.models import User
from .models import External, Plan, Datos_Facturacion, Pedido, Email_Confirmation, Factura, Password_Recovery
from editor.models import Project, Media, Mediatype, RenderState
from django.core.context_processors import csrf
from visionar.utils import validation
import visionar.config.environment as env
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

from visionar.utils.facelec.pyafipws.utils import verifica
from visionar.utils.facelec.pyafipws.wsfev1 import *
from visionar.utils.facelec.pyafipws import wsaa
import datetime
import decimal
import os, time
import socket
import sys
import traceback
from cStringIO import StringIO
from visionar.utils.facelec.pysimplesoap.pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper

import logging
logger = logging.getLogger(__name__)

def loginview(request):
    if request.user.is_authenticated():
        return redirect('/users/profile')
    else:
        return render(request, 'users/login.html', {'failed': False})
    
def auth_and_login(request, onsuccess='/create', onfail="/users/login/"):
    user = authenticate(username=request.POST['username'], password=request.POST['password'])
    if user is not None:
        if user.is_active:
            login(request, user)
            return redirect(onsuccess)
        return render(request, 'users/login.html', {"no_confirm": True})
    else:
        #return redirect(onfail)
        return render(request, 'users/login.html', {"failed": True}) 

def recover(request):
    if "email" in request.POST:
        email = request.POST['email']
        if User.objects.filter(email=request.POST['email']).exists():
            user = User.objects.get(email=request.POST['email'])
            if Password_Recovery.objects.filter(user=user).exists():
                Password_Recovery.objects.get(user=user).delete()
            pass_key = Password_Recovery(user=user)
            pass_key.save()
            
            sender = 'info@visionar.com.ar'
            receivers = [email]
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Recuperar password"
            msg['From'] = sender
            msg['To'] = email
            
            s = smtplib.SMTP('localhost')
            url = env.HOST + "users/recover_pass/" + user.username + "/" + pass_key .key

            text = "Ingrese a el siguiente link para cambiar el pass... " + url
            html = u'<html><head></head><body><h3>Recuperación de contraseña en visionar.com.ar</h3><p>Hola, <strong>' + user.username + '<strong></p><p>Dirigite a <a href="' + url + '">este link</a> para recuperar tu contraseña.</p></body></html>'.decode("utf-8")
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)
            
            s.sendmail(sender, receivers, msg.as_string())
            s.quit()
            return render(request, 'users/recovercheck.html')
        else:
            message = "Este mail no existe en nuestra base de datos"
    else:
        message = ""    
    
    return render(request, 'users/recover.html', {"message": message})

def recover_pass(request, username = "", key = ""):
    if username:
        try:
            us = User.objects.get(username=username)
            pr = Password_Recovery.objects.get(user=us)
            if str(pr.key) == str(key):
                return render(request, 'users/recover_fields.html', {'key': pr.key, 'username': us.username})
            else:
                return redirect("/users/login")
        except Exception, e:
            message = str(e)
            pass
        return redirect("/users/login")
    if "key" in request.POST:
        try:
            us = User.objects.get(username=str(request.POST["username"]))
            pr = Password_Recovery.objects.get(user=us)
            if pr.key == request.POST["key"]:
                us.set_password(request.POST["password"])
                us.save()
                pr.delete()
                return render(request, 'users/recover_fields.html', {'success': True})
            else:
                message = "El link utilizado no es valido"
        except Exception, e:
            message = "El link ha caducado o ya ha sido utilizado, por favor intente nuevamente" 
            pass
        return render(request, 'users/recover_fields.html', {'message': message})
    return redirect("/users/login/")


def create_user(username, email, password, first_name, last_name, company, phone):
    user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    user.set_password(password)
    user.is_active = False
    user.save()
    external = External(user=user ,company=company, phone=phone)
    external.save()
    key = Email_Confirmation(user=user)
    key.save()
    
    sender = 'info@visionar.com.ar'
    receivers = [email]
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Confirmación de email"
    msg['From'] = sender
    msg['To'] = email
    
    s = smtplib.SMTP('localhost')
    url = env.HOST + "users/validate/" + username + "/" + key.key

    text = "Ingrese a el siguiente link para activar su cuenta... " + url
    html = '''
    <html>
      <head></head>
      <body>
           <h3>Confirmación de mail visionar.com.ar</h3>
           <p>Hola, <strong>''' + username + '''<strong></p>
           <p>Dirigite a <a href="''' + url + '''">este link</a> para activar tu cuenta.</p>
           <p>Si no solicitaste una cuenta en visionar.com.ar podes obviar este mail</p>
      </body>
    </html>
    '''
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)
    
    s.sendmail(sender, receivers, msg.as_string())

    s.quit()
    logger.error(url)
    return user

#corresponde a /users/validate/
def email_confirmation(request, user, key):
    try:
        us = User.objects.get(username=user)
        em = Email_Confirmation.objects.get(user=us)
        if str(em.key) == str(key):
            us.is_active = True
            us.save()
            us.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, us)
            return redirect("/project/")
        else:
            message = "La clave es incorrecta"
    except Exception as e:
        message = "El usuario no existe"
        pass
    return render(request, 'users/confirmation.html', {"message": message})

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
        #return auth_and_login(request)
        return render(request, 'users/confirmation.html')
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
	proyecto = Project.objects.get(urlhash=project)
	if Datos_Facturacion.objects.filter(user=request.user):
		datos = Datos_Facturacion.objects.get(user=request.user)
	else:
		datos = None
	return render(request, "users/publicar.html", {"plan": plan, "datos": datos, "project": project, "proyecto":proyecto})

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
    
    pedido = Pedido(user=request.user, project=project, plan=Plan.objects.get(id=request.POST["plan"]), cantidad=1, tipo_pago=request.POST["forma-pago"], payment_state = "Pendiente", detalles=request.POST["detalles"])        
    pedido.save()
    return render(request, "users/pedido.html", {"pedido": pedido, "datos": datos, "proyecto":project})

def facturar(request, pedido_id):
	import time
	# Datos de facturacion
	pedido = Pedido.objects.get(id=pedido_id)
	user = pedido.user
	plan = pedido.plan
	datos_facturacion = Datos_Facturacion.objects.get(user=user)
	# Datos de conexion
	cache = None
	wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
	proxy = ""
	wrapper = "" #"pycurl"
	cacert = None #geotrust.crt"
	
	#Conectar
	wsfev1 = WSFEv1()
	wsfev1.LanzarExcepciones = True
	ok = wsfev1.Conectar(cache, wsdl, proxy, wrapper, cacert)

	if not ok:
		raise RuntimeError(wsfev1.Excepcion)

	# obteniendo el TA
	TA = "/home/vhcs2-virtual/videoeditor.com.ar/visionar/visionar/utils/facelec/pyafipws/TA.xml"
	if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
		tra = wsaa.create_tra(service="wsfe",ttl=36000)
		cms = wsaa.sign_tra(tra,"/home/vhcs2-virtual/videoeditor.com.ar/visionar/visionar/utils/facelec/certs/certificado.crt","/home/vhcs2-virtual/videoeditor.com.ar/visionar/visionar/utils/facelec/certs/privada")
		url = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" # "https://wsaa.afip.gov.ar/ws/services/LoginCms"
		ta_string = wsaa.call_wsaa(cms, url)
		open(TA,"w").write(ta_string)
	ta_string=open(TA).read()
	ta = SimpleXMLElement(ta_string)
	# fin TA

	if '--cuit' in sys.argv:
		cuit = sys.argv[sys.argv.index("--cuit")+1]
	else:
		cuit = "20276595955"

	#wsfev1.Cuit = cuit
	token = str(ta.credentials.token)
	sign = str(ta.credentials.sign)
	wsfev1.SetParametros(cuit, token, sign)

	tipo_cbte = 1 	# Factura A
	punto_vta = 0001
	cbte_nro = long(wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta) or 0)
	fecha = datetime.datetime.now().strftime("%Y%m%d")
	fecha2 = datetime.datetime.now().strftime("%Y-%m-%d")
	concepto = 2 				# Servicio
	tipo_doc = 80 				# Tipo CUIT
	nro_doc = datos_facturacion.cuit		# Numero CUIT
	cbt_desde = cbte_nro + 1
	cbt_hasta = cbte_nro + 1
	
	imp_total = "122.00"
	imp_tot_conc = "0.00"
	imp_neto = "100.00"
	imp_iva = "21.00"
	imp_trib = "1.00"
	imp_op_ex = "0.00"

	fecha_cbte = fecha
	fecha_venc_pago = fecha
	# Fechas del periodo del servicio facturado (solo si concepto = 1?)
	fecha_serv_desde = fecha; fecha_serv_hasta = fecha
	moneda_id = 'PES'; moneda_ctz = '1.000'

	resFact = wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
		cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
		imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
		fecha_serv_desde, fecha_serv_hasta, #--
		moneda_id, moneda_ctz)

	if tipo_cbte not in (1, 2):
		tipo = 19
		pto_vta = 2
		nro = 1234
		wsfev1.AgregarCmpAsoc(tipo, pto_vta, nro)

	base_imp = 100

	id = 5 # 21%
	base_im = 100
	importe = 21
	wsfev1.AgregarIva(id, base_imp, importe)

	import time
	t0 = time.time()
	cae = wsfev1.CAESolicitar()
	t1 = time.time()
	cae += "CAE: "
	cae += wsfev1.CAE

	factura = Factura(user=pedido.user,	
						cae = wsfev1.CAE,
						subtotal = imp_total,
						subtotal_neto = imp_neto,
						total_iva_1 = imp_iva,
						total_iva_2 = 0,
						otros_imp1 = 0,
						otros_imp2 = 0,
						descuento = 0,
						remito = '0',
						pedido = pedido,
						forma_pago = 'EF',
						pto_venta = punto_vta,
						numero = cbt_desde,
						letra = 'A',
						fecha = fecha2,
						iibb = 'Ing Brutos',
						link = ''
						)
	factura.save()

	link = "/media/facturas/pdf.pdf" #TODO: link a pdf de factura
	return render(request, "users/factura.html", {"link": link,
												"CAE": cae, 
												"CAE2":'34343434343',
												"resultado": wsfev1.Resultado,
												"msg":wsfev1.ErrMsg,
												"ultcomp":cbte_nro,
												"res":resFact}
				)
