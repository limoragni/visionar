#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Pruebas para WSFEv1 de AFIP (Factura Electrónica Mercado Interno sin detalle)"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"

DEBUG = False
HOMO = True
CONFIG_FILE = "rece.ini"

import unittest
import os, time, sys
from decimal import Decimal
import datetime

sys.path.append("/home/vicente/facelec")

from pyafipws.wsfev1 import WSFEv1
from pyafipws.wsaa import WSAA

import traceback
from cStringIO import StringIO
from fpdf import Template

WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
CUIT = 20276595955
CERT = "/home/vicente/facelec/certs/certificado.crt"
PRIVATEKEY = "/home/vicente/facelec/certs/privada"
CACERT = "/home/vicente/facelec/certs/afip_root_desa_ca.crt"
CACHE = "/home/vicente/pyafipws/cache"

# Autenticación:
wsaa = WSAA()
tra = wsaa.CreateTRA(service="wsfe")
cms = wsaa.SignTRA(tra, CERT, PRIVATEKEY)
wsaa.Conectar()
wsaa.LoginCMS(cms)

class Facturador():
	wsfev1 = WSFEv1()
	fepdf = FEPDF()
	tipos_fact = { 
		(1, 6, 11, 19): u'Factura', 
		(2, 7, 12, 20): u'Nota de Débito', 
		(3, 8, 13, 21): u'Nota de Crédito',
		(4, 9): u'Recibo', 
		(10, 5): u'Nota de Venta al contado', 
		(60, 61): u'Cuenta de Venta y Líquido producto',
		(63, 64): u'Liquidación',
		(91, ): u'Remito',
		(39, 40): u'???? (R.G. N° 3419)'}
	letras_fact = {(1, 2, 3, 4, 5, 39, 60, 63): 'A',
				   (6, 7, 8, 9, 10, 40, 61, 64): 'B',
				   (11, 12, 13): 'C',
				   (19, 20, 21): 'E',
				   (91, ): 'R',
				}
	
	def __main__(self):
		# Datos de la Factura
		self.factura = None
		self.Exception = self.Traceback = ""
		self.InstallDir = INSTALL_DIR
		self.Locale="es_AR.utf8"
		#self.FmtCantidad = self.FmtPrecio = "0.2" # no se que es
		self.CUIT = ''
		self.factura = {}
		self.datos = [] 
		self.elements = []
		self.pdf = {}
		self.log = StringIO()
		#sys.stdout = self.log
		#sys.stderr = self.log

	def setUp(self):
		#sys.argv.append("--trace")                  # TODO: use logging
		wsfev1 = wsfev1 = WSFEv1()
		wsfev1.Cuit = CUIT
		wsfev1.Token = wsaa.Token
		wsfev1.Sign = wsaa.Sign 
		wsfev1.Conectar(CACHE, WSDL)
	
	def getLastComp(self, tipo_cbte, pto_vta):
		"Prueba de autorización de un comprobante (obtención de CAE)"
		wsfev1 = self.wsfev1
		return wsfev1.CompUltimoAutorizado(tipo_cbte,pto_vta)
	

	def setHeader(self, nro_comp):
		"Prueba de autorización de un comprobante (obtención de CAE)"
		wsfev1 = self.wsfev1

		# datos generales del comprobante:
		punto_vta = 0001
		if not cbte_nro:
			# si no me especifícan nro de comprobante, busco el próximo
			cbte_nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)
			cbte_nro = long(cbte_nro) + 1
		fecha = datetime.datetime.now().strftime("%Y%m%d")
		tipo_doc = 80; nro_doc = "30000000007" ##"30500010912" # CUIT BNA
		cbt_desde = cbte_nro; cbt_hasta = cbt_desde
		imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
		imp_trib = "1.00"; imp_op_ex = "0.00"; imp_iva = "21.00"
		fecha_cbte = fecha
		# Fechas del período del servicio facturado (solo si concepto = 1?)
		if servicios:
			concepto = 3
			fecha_venc_pago = fecha
			fecha_serv_desde = fecha; fecha_serv_hasta = fecha
		else:
			concepto = 1
			fecha_venc_pago = fecha_serv_desde = fecha_serv_hasta = None
		moneda_id = 'PES'; moneda_ctz = '1.000'
		obs = "Observaciones Comerciales, libre"

		wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
			cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
			imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
			fecha_serv_desde, fecha_serv_hasta, #--
			moneda_id, moneda_ctz)


	def printPDF(self):
		from ConfigParser import SafeConfigParser

		DEBUG = '--debug' in sys.argv
				
		# leeo configuración (primer argumento o rece.ini por defecto)
		if len(sys.argv)>1 and not sys.argv[1].startswith("--"):
			CONFIG_FILE = sys.argv.pop(1)
		if DEBUG: print "CONFIG_FILE:", CONFIG_FILE

		config = SafeConfigParser()
		config.read(CONFIG_FILE)
		conf_fact = dict(config.items('FACTURA'))
		conf_pdf = dict(config.items('PDF'))
		# creo una factura de ejemplo
		tipo_cbte = 2
		punto_vta = 0001
		fecha = datetime.datetime.now().strftime("%Y%m%d")
		concepto = 3
		tipo_doc = 80; nro_doc = "30000000007"
		cbte_nro = 12345678
		imp_total = "122.00"; imp_tot_conc = "3.00"
		imp_neto = "100.00"; imp_iva = "21.00"
		imp_trib = "1.00"; imp_op_ex = "2.00"; imp_subtotal = "100.00"
		fecha_cbte = fecha; fecha_venc_pago = fecha
		# Fechas del período del servicio facturado (solo si concepto = 1?)
		fecha_serv_desde = fecha; fecha_serv_hasta = fecha
		moneda_id = 'PES'; moneda_ctz = '1.000'
		obs_generales = "Observaciones Generales, texto libre"
		obs_comerciales = "Observaciones Comerciales, texto libre"

		nombre_cliente = 'Joao Da Silva'
		domicilio_cliente = 'Rua 76 km 34.5 Alagoas'
		pais_dst_cmp = 16
		id_impositivo = 'PJ54482221-l'
		moneda_id = '012'
		moneda_ctz = 0.5
		forma_pago = '30 dias'
		incoterms = 'FOB'
		idioma_cbte = 1
		motivo = "11"

		cae = "61123022925855"
		fch_venc_cae = "20110320"
		
		fepdf.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
			cbte_nro, imp_total, imp_tot_conc, imp_neto,
			imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
			fecha_serv_desde, fecha_serv_hasta, 
			moneda_id, moneda_ctz, cae, fch_venc_cae, id_impositivo,
			nombre_cliente, domicilio_cliente, pais_dst_cmp, 
			obs_comerciales, obs_generales, forma_pago, incoterms, 
			idioma_cbte, motivo)
		
		tipo = 91
		pto_vta = 2
		nro = 1234
		fepdf.AgregarCmpAsoc(tipo, pto_vta, nro)
		tipo = 5
		pto_vta = 2
		nro = 1234
		fepdf.AgregarCmpAsoc(tipo, pto_vta, nro)
		
		tributo_id = 99
		desc = 'Impuesto Municipal Matanza'
		base_imp = "100.00"
		alic = "1.00"
		importe = "1.00"
		fepdf.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

		iva_id = 5 # 21%
		base_imp = 100
		importe = 21
		fepdf.AgregarIva(iva_id, base_imp, importe)
		
		u_mtx = 123456
		cod_mtx = 1234567890123
		codigo = "P0001"
		ds = "Descripcion del producto P0001\n" + "Lorem ipsum sit amet " * 10
		qty = 1.00
		umed = 7
		precio = 100.00
		bonif = 0.00
		iva_id = 5
		imp_iva = 21.00
		importe = 121.00
		despacho = u'Nº 123456'
		fepdf.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed, 
				precio, bonif, iva_id, imp_iva, importe, despacho)

		fepdf.AgregarDato("prueba", "1234")
		print "Prueba!"


fact = Facturador()
fact.setUp()
print fact.getLastComp(2,0001)
fact.printPDF()
