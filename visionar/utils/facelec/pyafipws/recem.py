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

"M�dulo de Intefase para archivos de texto (MATRIX mercado interno con detalle)"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.30c"

import datetime
import os
import sys
import time
import traceback
from ConfigParser import SafeConfigParser

# revisar la instalaci�n de pyafip.ws:
import wsaa, wsmtx
from php import SimpleXMLElement, SoapClient, SoapFault, date


HOMO = wsmtx.HOMO
DEBUG = False
PDB = False
XML = False
CONFIG_FILE = "rece.ini"

LICENCIA = """
recem.py: Interfaz de texto para generar Facturas Electr�nica MATRIX
Copyright (C) 2010 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para informaci�n adicional sobre garant�a, soporte t�cnico comercial
e incorporaci�n/distribuci�n en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

# definici�n del formato del archivo de intercambio:
N = 'Numerico'
A = 'Alfanumerico'
I = 'Importe'

if not '--pyfepdf' in sys.argv:
    TIPOS_REG = '0', '1', '2', '3', '4', '5'
    ENCABEZADO = [
        ('tipo_reg', 1, N), # 0: encabezado
        ('fecha_cbte', 10, A),
        ('tipo_cbte', 2, N),
        ('punto_vta', 4, N),
        ('cbt_desde', 8, N), 
        ('cbt_hasta', 8, N), 
        ('concepto', 1, N), # 1:bienes, 2:servicios,... 
        ('tipo_doc', 2, N), # 80
        ('nro_doc', 11, N), # 50000000016    
        ('imp_total', 15, I, 2), 
        ('imp_tot_conc', 15, I, 2), 
        ('imp_neto', 15, I, 2), 
        ('imp_subtotal', 15, I, 2), 
        ('imp_trib', 15, I, 2), 
        ('imp_op_ex', 15, I, 2), 
        ('moneda_id', 3, A),
        ('moneda_ctz', 10, I, 6), #10,6
        ('fecha_venc_pago', 10, A),   # opcional solo conceptos 2 y 3
        ('fecha_serv_desde', 10, A), # opcional solo conceptos 2 y 3
        ('fecha_serv_hasta', 10, A), # opcional solo conceptos 2 y 3
        ('cae', 14, N),
        ('fch_venc_cae', 10, A),
        ('resultado', 1, A), 
        ('motivos_obs', 1000, A),
        ('err_code', 6, A),
        ('err_msg', 1000, A),
        ('reproceso', 1, A),
        ('emision_tipo', 4, A),
        ('observaciones', 1000, A),  # observaciones (opcional)
        ]

    DETALLE = [
        ('tipo_reg', 1, N),     # 4: detalle item
        ('u_mtx', 10, N),
        ('cod_mtx', 30, A),
        ('codigo', 30, A),
        ('qty', 15, I, 3),      # deber�a ser 18,6 pero el DBF no lo soporta
        ('umed', 3, N),
        ('precio', 15, I, 3),   # deber�a ser 18,6 pero el DBF no lo soporta
        ('bonif', 15, I, 3),
        ('iva_id', 3, N),
        ('imp_iva', 15, I, 2),
        ('imp_subtotal', 15, I, 2),
        ('ds', 4000, A),
        ]

    TRIBUTO = [
        ('tipo_reg', 1, N),     # 1: tributo
        ('tributo_id', 3, A),   # c�digo de otro tributo
        ('desc', 100, A),       # descripci�n
        ('base_imp', 15, I, 2), 
        ('alic', 15, I, 2),     # no se usa...
        ('importe', 15, I, 2),  
        ]

    IVA = [
        ('tipo_reg', 1, N),     # 2: IVA
        ('iva_id', 3, A),       # c�digo de al�cuota
        ('base_imp', 15, I, 2), # no se usa... 
        ('importe', 15, I, 2),  
        ]

    CMP_ASOC = [
        ('tipo_reg', 1, N),     # 3: comprobante asociado
        ('tipo', 3, N),         
        ('pto_vta', 4, N),
        ('nro', 8, N), 
        ]

else:
    print "!" * 78
    print "importando formato segun pyfepdf"
    from formato_txt import ENCABEZADO, DETALLE, PERMISO, CMP_ASOC, IVA, TRIBUTO
    TIPOS_REG = '0', '5', '4', '3', '1'

def leer(linea, formato):
    dic = {}
    comienzo = 1
    for fmt in formato:    
        clave, longitud, tipo = fmt[0:3]
        if isinstance(longitud, tuple):
            longitud, dec = longitud
        else:
            dec = len(fmt)>3 and fmt[3] or 2
            
        valor = linea[comienzo-1:comienzo-1+longitud].strip()
        try:
            if tipo == N:
                if valor:
                    valor = str(int(valor))
                else:
                    valor = '0'
            elif tipo == I:
                if valor:
                    try:
                        if '.' in valor:
                            valor = float(valor)
                        else:
                            valor = valor.strip(" ")
                            valor = float(("%%s.%%0%sd" % dec) % (int(valor[:-dec] or '0'), int(valor[-dec:] or '0')))
                    except ValueError:
                        raise ValueError("Campo invalido: %s = '%s'" % (clave, valor))
                else:
                    valor = 0.00
            elif clave.lower().startswith("fec") and longitud <= 8:
                if valor:
                    valor = "%s-%s-%s" % (valor[0:4], valor[4:6], valor[6:8])
                else:
                    valor = None
            else:
                valor = valor.decode("ascii","ignore")
            if clave=='concepto':
                if PDB: import pdb;pdb.set_trace()
            dic[clave] = valor

            comienzo += longitud
        except Exception, e:
            if PDB: import pdb; pdb.set_trace()

            raise ValueError("Error al leer campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return dic

def escribir(dic, formato):
    linea = " " * 335
    comienzo = 1
    for fmt in formato:
        clave, longitud, tipo = fmt[0:3]
        if isinstance(longitud, tuple):
            longitud, dec = longitud
        else:
            dec = len(fmt)>3 and fmt[3] or 2
        try:
            if clave.capitalize() in dic:
                clave = clave.capitalize()
            s = dic.get(clave,"")
            if isinstance(s, unicode):
                s = s.encode("latin1")
            if s is None:
                valor = ""
            else:
                valor = str(s)
            if tipo == N and valor and valor!="NULL":
                valor = ("%%0%dd" % longitud) % int(valor)
            elif tipo == I and valor:
                valor = ("%%0%dd" % longitud) % int(float(valor)*(10**dec))
            elif clave.lower().startswith("fec") and longitud <= 8 and valor:
                ##import pdb; pdb.set_trace()
                valor = valor.replace("-", "")
            else:
                valor = ("%%-0%ds" % longitud) % valor
            if len(valor) != longitud:
                print "Longitud incorrecta!", clave, valor
                if PDB: import pdb;pdb.set_trace()
                valor = " "* (longitud-len(valor)) + valor
            linea = linea[:comienzo-1] + valor + linea[comienzo-1+longitud:]
            comienzo += longitud
        except Exception, e:
            import pdb; pdb.set_trace()
            raise ValueError("Error al escribir campo %s pos %s val '%s': %s" % (
                clave, comienzo, valor, str(e)))
    return linea + "\n"

def autenticar(cert, privatekey, url):
    "Obtener el TA"
    TA = "TA-wsmtx.xml"
    ttl = 60*60*5
    if not os.path.exists(TA) or os.path.getmtime(TA)+(ttl)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsmtxca",ttl=ttl)
        cms = wsaa.sign_tra(str(tra),str(cert),str(privatekey))
        ta_string = wsaa.call_wsaa(cms,wsaa_url,trace=DEBUG)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    return token, sign

def autorizar(ws, entrada, salida, informar_caea=False):
    tributos = []
    ivas = []
    cbtasocs = []
    encabezado = []
    detalles = []
    if '/dbf' in sys.argv:
        import dbf
        if DEBUG: print "Leyendo DBF..."

        formatos = [('Encabezado', ENCABEZADO, encabezado), ('Tributo', TRIBUTO, tributos), ('Iva', IVA, ivas), ('Comprobante Asociado', CMP_ASOC, cbtasocs), ('Detalles', DETALLE, detalles)]
        for nombre, formato, ld in formatos:
            filename = conf_dbf.get(nombre.lower(), "%s.dbf" % nombre[:8])
            if DEBUG: print "leyendo tabla", nombre, filename
            tabla = dbf.Table(filename)
            for reg in tabla:
                r = {}
                d = reg.scatter_fields() 
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    #import pdb; pdb.set_trace()
                    v = d[clave.replace("_","")[:10]]
                    r[clave] = v
                ld.append(r)    
            tabla.close()
        encabezado = encabezado[0]
    else:
        for linea in entrada:
            if str(linea[0])==TIPOS_REG[0]:
                encabezado = leer(linea, ENCABEZADO)
                if 'cbte_nro' in encabezado:
                    print "*" * 80
                    print "cbte_nro", encabezado['cbte_nro']
                    encabezado['cbt_desde'] = encabezado['cbte_nro']
                    encabezado['cbt_hasta'] = encabezado['cbte_nro']
                    del encabezado['cbte_nro']
            elif str(linea[0])==TIPOS_REG[1]:
                tributo = leer(linea, TRIBUTO)
                tributos.append(tributo)
            elif str(linea[0])==TIPOS_REG[2]:
                iva = leer(linea, IVA)
                ivas.append(iva)
            elif str(linea[0])==TIPOS_REG[3]:
                cbtasoc = leer(linea, CMP_ASOC)
                if 'cbte_punto_vta' in cbteasoc:
                    cbtasoc['tipo'] = cbtasoc['cbte_tipo']
                    cbtasoc['pto_vta'] = cbtasoc['cbte_punto_vta']
                    cbtasoc['nro'] = cbtasoc['cbte_nro']
                cbtasocs.append(cbtasoc)
            elif str(linea[0])==TIPOS_REG[4]:
                detalle = leer(linea, DETALLE)
                detalles.append(detalle)
                if 'imp_subtotal' not in detalle:
                    detalle['imp_subtotal'] = detalle['importe']
            else:
                print "Tipo de registro incorrecto:", linea[0]
       
    if informar_caea:
        if '/testing' in sys.argv:
            encabezado['cae'] = '21353598240916'
            encabezado['fch_venc_cae'] = '2011-09-15'
        encabezado['caea'] = encabezado['cae']

    if 'imp_subtotal' not in encabezado:
        encabezado['imp_subtotal'] = encabezado['imp_neto'] + encabezado['imp_tot_conc']

    ws.CrearFactura(**encabezado)
    for detalle in detalles:
        ws.AgregarItem(**detalle)
    for tributo in tributos:
        ws.AgregarTributo(**tributo)
    for iva in ivas:
        ws.AgregarIva(**iva)
    for cbtasoc in cbtasocs:
        ws.AgregarCmpAsoc(**cbtasoc)

    if DEBUG:
        print '\n'.join(["%s='%s'" % (k,str(v)) for k,v in ws.factura.items()])
    if not DEBUG or raw_input("Facturar?")=="S":
        if not informar_caea:
            cae = ws.AutorizarComprobante()
            dic = ws.factura
        else:
            cae = ws.InformarComprobanteCAEA()
            dic = ws.factura
        dic.update({
            'cae':cae,
            'fch_venc_cae': ws.Vencimiento,
            'resultado': ws.Resultado,
            'motivos_obs': ws.Obs,
            'err_code': ws.ErrCode,
            'err_msg': ws.ErrMsg,
            'reproceso': ws.Reproceso,
            'emision_tipo': ws.EmisionTipo,
            })
        escribir_factura(dic, salida)
        print "NRO:", dic['cbt_desde'], "Resultado:", dic['resultado'], "%s:" % ws.EmisionTipo,dic['cae'],"Obs:",dic['motivos_obs'].encode("ascii", "ignore"), "Err:", dic['err_msg'].encode("ascii", "ignore"), "Reproceso:", dic['reproceso']

def escribir_factura(dic, archivo):
    dic['tipo_reg'] = TIPOS_REG[0]
    dic['cbte_nro'] = dic.get('cbt_desde')
    archivo.write(escribir(dic, ENCABEZADO))
    if 'tributos' in dic:
        for it in dic['tributos']:
            it['tipo_reg'] = TIPOS_REG[1]
            archivo.write(escribir(it, TRIBUTO))
    if 'iva' in dic:
        for it in dic['iva']:
            it['tipo_reg'] = TIPOS_REG[2]
            archivo.write(escribir(it, IVA))
    if 'cbtes_asoc' in dic:
        for it in dic['cbtes_asoc']:
            it['tipo_reg'] = TIPOS_REG[3]
            archivo.write(escribir(it, CMP_ASOC))
    if 'detalles' in dic:
        for it in dic['detalles']:
            it['tipo_reg'] = TIPOS_REG[4]
            it['importe'] = it['imp_subtotal']
            archivo.write(escribir(it, DETALLE))
            
    if '/dbf' in sys.argv:
        import dbf
        if DEBUG: print "Creando DBF..."

        tablas = {}
        formatos = [('Encabezado', ENCABEZADO, [dic]), ('Tributo', TRIBUTO, dic.get('tributos', [])), ('Iva', IVA, dic.get('iva', [])), ('Comprobante Asociado', CMP_ASOC, dic.get('cbtes_asoc', [])), ('Detalles', DETALLE, dic.get('detalles', []))]
        for nombre, formato, l in formatos:
            campos = []
            claves = []
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                if longitud>250:
                    tipo = "M" # memo!
                elif tipo == A:
                    tipo = "C(%s)" % longitud 
                elif tipo == N:
                    tipo = "N(%s,0)" % longitud 
                elif tipo == I:
                    tipo = "N(%s,%s)" % (longitud, dec)
                campo = "%s %s" % (clave.replace("_","")[:10], tipo)
                if DEBUG: print "tabla %s campo %s" %  (nombre, campo)
                campos.append(campo)
                claves.append(clave.replace("_","")[:10])
            filename = conf_dbf.get(nombre.lower(), "%s.dbf" % nombre[:8])
            if DEBUG: print "escribiendo tabla", nombre, filename
            if '/delete' in sys.argv:
                if DEBUG: print "eliminando", filename
                os.unlink(filename)
            tabla = dbf.Table(filename, campos)

            for d in l:
                r = {}
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    v = d.get(clave, None)
                    if DEBUG: print clave,v, tipo
                    if v is None and tipo == A:
                        v = ''
                    if (v is None or v=='') and tipo in (I, N):
                        v = 0
                    if tipo == A:
                        v = unicode(v)
                    r[clave.replace("_","")[:10]] = v
                registro = tabla.append(r)
            tabla.close()

def depurar_xml(client):
    global wsmtxca_xml_dir
    fecha = time.strftime("%Y%m%d%H%M%S")
    f=open(os.path.join(wsmtxca_xml_dir, "request-%s.xml" % fecha),"w")
    f.write(client.xml_request)
    f.close()
    f=open(os.path.join(wsmtxca_xml_dir, "response-%s.xml" % fecha),"w")
    f.write(client.xml_response)
    f.close()

if __name__ == "__main__":
    if '/ayuda' in sys.argv:
        print LICENCIA
        print
        print "Opciones: "
        print " /ayuda: este mensaje"
        print " /dummy: consulta estado de servidores"
        print " /prueba: genera y autoriza una factura de prueba (no usar en producci�n!)"
        print " /ult: consulta �ltimo n�mero de comprobante"
        print " /debug: modo depuraci�n (detalla y confirma las operaciones)"
        print " /formato: muestra el formato de los archivos de entrada/salida"
        print " /get: recupera datos de un comprobante autorizado previamente (verificaci�n)"
        print " /xml: almacena los requerimientos y respuestas XML (depuraci�n)"
        print " /dbf: lee y almacena la informaci�n en tablas DBF"
        print
        print "Ver rece.ini para par�metros de configuraci�n (URL, certificados, etc.)"
        sys.exit(0)

    if '/debug'in sys.argv:
        DEBUG = True
        print "VERSION", __version__, "HOMO", HOMO

    if len(sys.argv)>1 and sys.argv[1][0] not in "-/":
        CONFIG_FILE = sys.argv.pop(1)
    if DEBUG: print "CONFIG_FILE:", CONFIG_FILE

    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    #print CONFIG_FILE
    cert = config.get('WSAA','CERT')
    privatekey = config.get('WSAA','PRIVATEKEY')
    cuit = config.get('WSMTXCA','CUIT')
    if '/entrada' in sys.argv:
        entrada = sys.argv[sys.argv.index("/entrada")+1]
    else:
        entrada = config.get('WSMTXCA','ENTRADA')
    salida = config.get('WSMTXCA','SALIDA')
    
    if config.has_option('WSAA','URL') and not HOMO:
        wsaa_url = config.get('WSAA','URL')
    else:
        wsaa_url = wsaa.WSAAURL
    if config.has_option('WSMTXCA','URL') and not HOMO:
        wsmtxca_url = config.get('WSMTXCA','URL')
    else:
        wsmtxca_url = None

    if config.has_option('WSMTXCA','REPROCESAR'):
        wsmtxca_reprocesar = config.get('WSMTXCA','REPROCESAR') == 'S'
    else:
        wsmtxca_reprocesar = None

    if config.has_option('WSMTXCA', 'XML_DIR'):
        wsmtxca_xml_dir = config.get('WSMTXCA', 'XML_DIR')
    else:
        wsmtxca_xml_dir = "."

    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
        if DEBUG: print "conf_dbf", conf_dbf
    else:
        conf_dbf = {}

    if '/xml'in sys.argv:
        XML = True

    if DEBUG:
        print "wsaa_url %s\nwsmtxca_url %s\ncuit %s" % (wsaa_url, wsmtxca_url, cuit)
    
    try:
        ws = wsmtx.WSMTXCA()
        ws.Conectar("", wsmtxca_url)
        ws.Cuit = cuit
        if wsmtxca_reprocesar is not None:
            ws.Reprocesar = wsmtxca_reprocesar

        if '/dummy' in sys.argv:
            print "Consultando estado de servidores..."
            ws.Dummy()
            print "AppServerStatus", ws.AppServerStatus
            print "DbServerStatus", ws.DbServerStatus
            print "AuthServerStatus", ws.AuthServerStatus
            sys.exit(0)

        if '/formato' in sys.argv:
            print "Formato:"
            for msg, formato in [('Encabezado', ENCABEZADO), ('Tributo', TRIBUTO), ('Iva', IVA), ('Comprobante Asociado', CMP_ASOC), ('Detalle', DETALLE)]:
                comienzo = 1
                print "== %s ==" % msg
                for fmt in formato:
                    clave, longitud, tipo = fmt[0:3]
                    if isinstance(longitud, tuple):
                        longitud, dec = longitud
                    else:
                        dec = len(fmt)>3 and fmt[3] or 2
                    print " * Campo: %-20s Posici�n: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                        clave, comienzo, longitud, tipo, dec)
                    comienzo += longitud
            sys.exit(0)

        token, sign = autenticar(cert, privatekey, wsaa_url)
        ws.Token = token
        ws.Sign = sign
        
        if '/puntosventa' in sys.argv:
            print "Consultando puntos de venta CAE..."
            print '\n'.join(ws.ConsultarPuntosVentaCAE())
            print "Consultando puntos de venta CAEA..."
            print '\n'.join(ws.ConsultarPuntosVentaCAEA())
            sys.exit(0)
            
        if '/prueba' in sys.argv:
            # generar el archivo de prueba para la pr�xima factura
            tipo_cbte = 6
            punto_vta = 4000
            cbte_nro = ws.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            concepto = 3
            tipo_doc = 80; nro_doc = "30000000007"
            cbte_nro = long(cbte_nro) + 1
            cbt_desde = cbte_nro; cbt_hasta = cbt_desde
            imp_total = "121.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_trib = "0.00"; imp_op_ex = "0.00"; imp_subtotal = "100.00"
            fecha_cbte = fecha; fecha_venc_pago = fecha
            # Fechas del per�odo del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = fecha; fecha_serv_hasta = fecha
            moneda_id = 'PES'; moneda_ctz = '1.000'
            obs = "Observaciones Comerciales, libre"

            ws.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
                fecha_serv_desde, fecha_serv_hasta, #--
                moneda_id, moneda_ctz, obs)
            
            if tipo_cbte not in (1, 2, 6, 7):
                tipo = 1
                pto_vta = 2
                nro = 1234
                ws.AgregarCmpAsoc(tipo, pto_vta, nro)
            
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = 100
            alic = 1
            importe = 1
            #ws.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_imp = 100
            importe = 21
            ws.AgregarIva(iva_id, base_imp, importe) 
            
            u_mtx = 123456
            cod_mtx = 1234567890123
            codigo = "P0001"
            ds = "Descripcion del producto P0001"
            qty = 1.00
            umed = 7
            if tipo_cbte in (6, 7, 8):
                precio = 121.00
            else:
                precio = 100.00
            bonif = 0.00
            iva_id = 5
            imp_iva = 21.00
            imp_subtotal = 121.00
            ws.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                        iva_id, imp_iva, imp_subtotal)

            if tipo_cbte not in (6, 7, 8):
                ws.AgregarItem(u_mtx, cod_mtx, codigo, "PRUEBA", 1, 7, 1.00, 0, 
                            iva_id, 0.21, 1.21)
                ws.AgregarItem(1, "DESC", "DESC", "Descuento", 0, 99, 0, 0, 
                            iva_id, 0.21, 1.21)
            else:
                ws.AgregarItem(u_mtx, cod_mtx, codigo, "PRUEBA", 1, 7, 1.21, 0, 
                            iva_id, 0.0, 1.21)
                ws.AgregarItem(1, "DESC", "DESC", "Descuento", 0, 99, 0, 0, 
                            iva_id, 0.0, 1.21)
            
            f_entrada = open(entrada,"w")
                
            if DEBUG:
                print ws.factura

            dic = ws.factura
            escribir_factura(dic, f_entrada)            
            f_entrada.close()
      
        if '/ult' in sys.argv:
            print "Consultar ultimo numero:"
            i = sys.argv.index("/ult")
            if i+2<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
            ult_cbte = ws.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            print "Ultimo numero: ", ult_cbte
            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': punto_vta, 
                              'cbt_desde': ult_cbte, 
                              'fecha_cbte': ws.FechaCbte, 
                              }, open(salida,"w"))
            sys.exit(0)

        if '/get' in sys.argv:
            print "Recuperar comprobante:"
            i = sys.argv.index("/get")
            if i+3<len(sys.argv):
               tipo_cbte = int(sys.argv[i+1])
               punto_vta = int(sys.argv[i+2])
               cbte_nro = int(sys.argv[i+3])
            else:
               tipo_cbte = int(raw_input("Tipo de comprobante: "))
               punto_vta = int(raw_input("Punto de venta: "))
               cbte_nro = int(raw_input("Numero de comprobante: "))
            ws.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)

            print "FechaCbte = ", ws.FechaCbte
            print "CbteNro = ", ws.CbteNro
            print "PuntoVenta = ", ws.PuntoVenta
            print "ImpTotal =", ws.ImpTotal
            print "CAE = ", ws.CAE
            print "Vencimiento = ", ws.Vencimiento
            print "EmisionTipo = ", ws.EmisionTipo

            depurar_xml(ws.client)
            escribir_factura({'tipo_cbte': tipo_cbte, 
                              'punto_vta': ws.PuntoVenta, 
                              'cbt_desde': ws.CbteNro, 
                              'fecha_cbte': ws.FechaCbte, 
                              'imp_total': ws.ImpTotal, 
                              'cae': ws.CAE, 
                              'fch_venc_cae': ws.Vencimiento,  
                              'emision_tipo': ws.EmisionTipo, 
                              }, open(salida,"w"))

            sys.exit(0)

        if '/solicitarcaea' in sys.argv:
            if len(sys.argv) > sys.argv.index("/solicitarcaea")+1:
                periodo = sys.argv[sys.argv.index("/solicitarcaea")+1]
                orden = sys.argv[sys.argv.index("/solicitarcaea")+2]
            else:
                periodo = raw_input("Periodo (a�o-mes, ej 201108): ")
                orden = raw_input("Orden (quincena, 1 u 2): ")
                
            if DEBUG: 
                print "Solicitando CAEA para periodo %s orden %s" % (periodo, orden)
            
            caea = ws.SolicitarCAEA(periodo, orden)
            print "CAEA:", caea

            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error

            depurar_xml(ws.client)

            if not caea:
                if DEBUG: 
                    print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
                caea = ws.ConsultarCAEA(periodo, orden)
                print "CAEA:", caea
                
            if DEBUG:
                print "Periodo:", ws.Periodo 
                print "Orden:", ws.Orden 
                print "FchVigDesde:", ws.FchVigDesde 
                print "FchVigHasta:", ws.FchVigHasta 
                print "FchTopeInf:", ws.FchTopeInf 
                print "FchProceso:", ws.FchProceso

            escribir_factura({'cae': caea, 
                              'emision_tipo': "CAEA", 
                             }, open(salida,"w"))
                              
            sys.exit(0)

        if '/consultarcaea' in sys.argv:
            periodo = raw_input("Periodo: ")
            orden = raw_input("Orden: ")

            if DEBUG: 
                print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
            
            caea = ws.ConsultarCAEA(periodo, orden)
            print "CAEA:", caea

            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
                
            if DEBUG:
                print "Periodo:", ws.Periodo 
                print "Orden:", ws.Orden 
                print "FchVigDesde:", ws.FchVigDesde 
                print "FchVigHasta:", ws.FchVigHasta 
                print "FchTopeInf:", ws.FchTopeInf
                print "FchProceso:", ws.FchProceso
            sys.exit(0)

            
        if '/informarcaeanoutilizado' in sys.argv:
            caea = raw_input("CAEA: ")
            if DEBUG: 
                print "Informando CAEA no utilizado: %s" % (caea, )
            ok = ws.InformarCAEANoUtilizado(caea)
            print "Resultado:", ok
            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
            sys.exit(0)

        if '/informarcaeanoutilizadoptovta' in sys.argv:
            caea = raw_input("CAEA: ")
            pto_vta = raw_input("Punto de Venta: ")
            if DEBUG: 
                print "Informando CAEA no utilizado: %s pto_vta %s" % (caea, pto_vta)
            ok = ws.InformarCAEANoUtilizadoPtoVta(caea, pto_vta)
            print "Resultado:", ok
            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
            sys.exit(0)

        if '/consultarptosvtacaeanoinformados' in sys.argv:
            caea = raw_input("CAEA: ")
            if DEBUG: 
                print "Consultando PtosVta CAEA: %s" % (caea)
            ptos_vta = ws.ConsultarPtosVtaCAEANoInformados(caea)
            print "Resultado:", '\n'.join(ptos_vta)
            if ws.Errores:
                print "Errores:"
                for error in ws.Errores:
                    print error
            sys.exit(0)
            
        f_entrada = f_salida = None
        try:
            f_entrada = open(entrada,"r")
            f_salida = open(salida,"w")
            try:
                if DEBUG: print "Autorizando usando entrada:", entrada
                autorizar(ws, f_entrada, f_salida, '/informarcaea' in sys.argv)
            except SoapFault:
                XML = True
                raise
        finally:
            if f_entrada is not None: f_entrada.close()
            if f_salida is not None: f_salida.close()
            if XML:
                depurar_xml(ws.client)
        sys.exit(0)
    
    except SoapFault, e:
        print e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        e_str = unicode(e).encode("ascii","ignore")
        if not e_str:
            e_str = repr(e)
        print e_str
        escribir_factura({'err_msg': e_str,
                         }, open(salida,"w"))
        ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
        open("traceback.txt", "wb").write('\n'.join(ex))

        if DEBUG:
            raise
        sys.exit(5)
