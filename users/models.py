from django.db import models
from django.contrib.auth.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from editor.models import Project
import base64
import hashlib
import os

def avatar_file_upload(instance, filename):
    _, ext = os.path.splitext(filename)
    format =  str(instance.user.username) + ext
    return os.path.join("avatars", format)

class External(models.Model):
	user 	= models.OneToOneField(User)
	phone 	= models.CharField(max_length=100)
	company = models.CharField(max_length=100)
	avatar  = ThumbnailerImageField(upload_to=avatar_file_upload, null=True)

	@property
	def thumb(self):
		return self.avatar['profile'].url

class Email_Confirmation(models.Model):
	user = models.OneToOneField(User)
	key  = models.CharField(max_length=200)
	
	def save(self):
		super(Email_Confirmation, self).save()
		if not self.key:
			hasher = hashlib.sha1(self.user.username)
			self.key = base64.urlsafe_b64encode(hasher.digest()[0:10])
			self.save()

class Password_Recovery(models.Model):
	user = models.OneToOneField(User)
	key  = models.CharField(max_length=200)
	
	def save(self):
		super(Password_Recovery, self).save()
		if not self.key:
			hasher = hashlib.sha1(self.user.username)
			self.key = base64.urlsafe_b64encode(hasher.digest()[0:10])
			self.save()


class Datos_Facturacion(models.Model):
	TIPO_IVAS = (
		('Responsable Inscripto', 	'Responsable Inscripto'),
		('Responsable No Inscripto', 'Responsable No Inscripto'),
		('Exento', 	'Exento'),
		('Monotributista', 'Monotributista'),
		('Consumidor Final','Consumidor Final')
	)
	user			= models.ForeignKey(User, unique=True)
	tipo_iva		= models.CharField(max_length=100, choices=TIPO_IVAS)
	cuit 			= models.CharField(max_length=11)
	razon_social	= models.CharField(max_length=100)
	nombre_fantasia	= models.CharField(max_length=200)
	direccion		= models.CharField(max_length=250)
	localidad		= models.CharField(max_length=100)
	provincia		= models.CharField(max_length=100)
	pais			= models.CharField(max_length=100)
	codigo_iva		= models.CharField(max_length=20)


	class Admin:
		pass	

class Plan(models.Model):
	CONTRATACION_MINIMA_OPS = (
		('DIA', 'Dia'),
		('SEMANA', 'Semana'),
		('MES', 'Mes')
	)

	nombre 				= models.CharField(max_length=50)
	pasadas_prime 		= models.IntegerField()
	pasadas_normal 		= models.IntegerField()
	contratacion_minima = models.CharField(max_length=10, choices=CONTRATACION_MINIMA_OPS)
	bonificacion		= models.DecimalField(max_digits=4, decimal_places=2)
	costo				= models.DecimalField(max_digits=7, decimal_places=2)
	disponible			= models.BooleanField()

	
	@property
	def descuento(self):
		percentage = self.bonificacion / 100
		desc = self.costo * percentage
		return "{:.2f}".format(desc)

	@property
	def total(self):
		percentage = self.bonificacion / 100
		desc = self.costo * percentage
		total = self.costo - desc
		return "{:.2f}".format(total)

	def __unicode__(self):
		return self.nombre

	class Admin:
		pass

class Pedido(models.Model):
	TIPO_PAGO_OPS = (
		('Mercadopago', 'Mercadopago'),
		('Tarjeta', 'Tarjeta'),
		('Deposito', 'Deposito')
	) 
	PAYMENT_STATES_CHOICES = (
		('Pendiente', 'Pendiente'),
		('Pagado', 'Pagado')
	)
	
	user			= models.ForeignKey(User)	
	project			= models.ForeignKey(Project)
	fecha			= models.DateTimeField(auto_now=True)
	plan			= models.ForeignKey(Plan)
	detalles		= models.TextField()
	cantidad		= models.IntegerField()
	tipo_pago		= models.CharField(max_length=100, choices=TIPO_PAGO_OPS)
	payment_state 	= models.CharField(max_length=10,choices=PAYMENT_STATES_CHOICES)

	def __unicode__(self):
		return self.detalles

	class Admin:
		pass	
	

class Factura(models.Model):
	FORMAS_PAGO = (
		('EF', 'Efectivo'),
		('CtaCte', 'Cuenta Corriente'),
		('Cheque', 'Cheque')
	)
	user			= models.ForeignKey(User)
	cae				= models.CharField(max_length=20)
	subtotal		= models.DecimalField(max_digits=7, decimal_places=2) # Total de los items desgravados sin ningun impuesto
	subtotal_neto	= models.DecimalField(max_digits=7, decimal_places=2) # Total de los items desgravados mas el/los IVAs (21 y 10,5) 
	total_iva_1		= models.DecimalField(max_digits=7, decimal_places=2) # 21
	total_iva_2		= models.DecimalField(max_digits=7, decimal_places=2) # 10,5
	otros_imp1		= models.DecimalField(max_digits=7, decimal_places=2) # Impuestos Municipales
	otros_imp2		= models.DecimalField(max_digits=7, decimal_places=2) # Otros impuestos
	descuento		= models.DecimalField(max_digits=7, decimal_places=2) # Descuento sobre el total de la facturacion
	remito			= models.CharField(max_length=15)
	pedido			= models.ForeignKey(Pedido)
	forma_pago		= models.CharField(max_length=15, choices=FORMAS_PAGO)
	pto_venta		= models.CharField(max_length=4)
	numero			= models.IntegerField()
	letra			= models.CharField(max_length=1)
	fecha			= models.DateField()
	iibb			= models.CharField(max_length=10) # Ingresos Brutos
	link 			= models.CharField(max_length=200)

	class Admin:
		pass

class Item_Factura(models.Model):
	factura			= models.ForeignKey(Factura)
	codigo			= models.CharField(max_length=15)
	descripcion		= models.CharField(max_length=100)
	unidad			= models.CharField(max_length=2)
	cantidad		= models.IntegerField()
	bonificacion	= models.DecimalField(max_digits=5,decimal_places=2) # En porcentaje
	precio			= models.DecimalField(max_digits=7,decimal_places=2)

	class Admin:
		pass


