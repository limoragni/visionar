import datetime
import decimal
import os
import sys
import traceback
from cStringIO import StringIO
from decimal import Decimal
from fpdf import Template
from pyfepdf import *


fepdf = FEPDF()
config = SafeConfigParser()
config.read(CONFIG_FILE)
conf_fact = dict(config.items('FACTURA'))
conf_pdf = dict(config.items('PDF'))

# cargo el formato CSV por defecto (factura.csv)
fepdf.CargarFormato(conf_fact.get("formato", "factura.csv"))

fepdf.FmtCantidad = conf_fact.get("fmt_cantidad", "0.2")
fepdf.FmtPrecio = conf_fact.get("fmt_precio", "0.2")

# creo una factura de ejemplo
tipo_cbte = 2
punto_vta = 4000
fecha = datetime.datetime.now().strftime("%Y%m%d")
concepto = 3
tipo_doc = 80; nro_doc = "30000000007"
cbte_nro = 12345678
imp_total = "122.00"; imp_tot_conc = "3.00"
imp_neto = "100.00"; imp_iva = "21.00"
imp_trib = "1.00"; imp_op_ex = "2.00"; imp_subtotal = "100.00"
fecha_cbte = fecha; fecha_venc_pago = fecha

fecha_serv_desde = fecha; fecha_serv_hasta = fecha
moneda_id = 'PES'; moneda_ctz = '1.000'
obs_generales = "Observaciones Generales, texto libre"
obs_comerciales = "Observaciones Comerciales, texto libre"

# Imprimo un factura de prueba. TODO: Parametrizar
nombre_cliente = 'Enrique Melenzana'
domicilio_cliente = 'Rua 76 km 34.5 Alagoas'
pais_dst_cmp = 16
id_impositivo = 'PJ54482221-l' # ?? No se que es
moneda_id = '012'
moneda_ctz = 0.5
forma_pago = '30 dias'
incoterms = 'FOB'
idioma_cbte = 1
motivo = "11"

cae = "61123022925855" # 
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
despacho = u'N 123456'
fepdf.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed, 
		precio, bonif, iva_id, imp_iva, importe, despacho)

fepdf.AgregarDato("prueba", "1234")

