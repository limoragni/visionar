from django.db import models
from django.contrib.auth.models import User
from editor.models import Project

class External(models.Model):
	user = models.OneToOneField(User)
	phone = models.CharField(max_length=100)
	company = models.CharField(max_length=100)

class Datos_Facturacion(models.Model):
	TIPO_IVAS = (
		('RI', 	'Responsable Inscripto'),
		('RNI', 'Responsable No Inscripto'),
		('EX', 	'Exento'),
		('MON', 'Monotributista'),
		('CF',	'Consumidor Final')
	)
	user			= models.ForeignKey(User)
	tipo_iva		= models.CharField(max_length=100, choices=TIPO_IVAS)
	cuit 			= models.CharField(max_length=10)
	razon_social	= models.CharField(max_length=100)
	nombre_fantasia	= models.CharField(max_length=200)
	direccion		= models.CharField(max_length=250)
	localidad		= models.CharField(max_length=100)
	provincia		= models.CharField(max_length=100)
	pais			= models.CharField(max_length=100)
	codigo_iva		= models.CharField(max_length=20)


	class Admin:
		pass	

class Pedido(models.Model):
	user			= models.ForeignKey(User)	
	project			= models.ForeignKey(Project)
	fecha			= models.DateField()
	plan			= models.CharField(max_length=10)
	detalles		= models.TextField()
	importe			= models.DecimalField(max_digits=7,decimal_places=2)

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
	pedido			= models.ForeignKey(Pedido)

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


