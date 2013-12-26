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

"""M�dulo para Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP Disp. 3683/11
seg�n Especificaci�n T�cnica para Pruebas de Servicios v2 (2013)"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.12a"

import os
import socket
import sys
import datetime, time
import traceback
import pysimplesoap.client
from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, \
                                set_http_wrapper
from pysimplesoap.simplexml import SimpleXMLElement
from cStringIO import StringIO

# importo funciones compartidas:
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, dar_nombre_campo_dbf

HOMO = True
TYPELIB = False

WSDL = "https://servicios.pami.org.ar/trazamed.WebService?wsdl"
LOCATION = "https://servicios.pami.org.ar/trazamed.WebService"
#WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl"

# Formato de MedicamentosDTO, MedicamentosDTODHSerie, MedicamentosDTOFraccion  
MEDICAMENTOS = [
    ('f_evento', 10, A),                # formato DD/MM/AAAA
    ('h_evento', 5, A),                 # formato HH:MM
    ('gln_origen', 13, A),
    ('gln_destino', 13, A),
    ('n_remito', 20, A),
    ('n_factura', 20, A),
    ('vencimiento', 10, A),
    ('gtin', 14, A),
    ('lote', 20, A),
    ('numero_serial', 20, A),
    ('desde_numero_serial', 20, A),     # sendMedicamentosDHSerie
    ('hasta_numero_serial', 20, A),     # sendMedicamentosDHSerie
    ('id_obra_social', 9, N),
    ('id_evento', 3, N),
    ('cuit_origen', 11, A),
    ('cuit_destino', 11, A),
    ('apellido', 50, A),
    ('nombres', 100, A),
    ('tipo_documento', 2, N),           # 96: DNI,80: CUIT
    ('n_documento', 10, A),
    ('sexo', 1, A),                     # M o F
    ('direccion', 100, A),
    ('numero', 10, A),
    ('piso', 5, A),
    ('depto', 5, A),
    ('localidad', 50, A),
    ('provincia', 100, A),
    ('n_postal', 8, A),
    ('fecha_nacimiento', 100, A),
    ('telefono', 30, A),
    ('nro_asociado', 30, A),
    ('cantidad', 3, N),                 # sendMedicamentosFraccion
    ('codigo_transaccion', 14, A),
]

# Formato para TransaccionPlainWS (getTransaccionesNoConfirmadas)
TRANSACCIONES = [
    ('_id_transaccion', 14, A), 
    ('_id_transaccion_global', 14, A),
    ('_f_evento', 10, A),
    ('_f_transaccion', 16, A),          # formato DD/MM/AAAA HH:MM
    ('_gtin', 14, A),
    ('_lote', 20, A), 
    ('_numero_serial', 20, A),
    ('_nombre', 200, A),
    ('_d_evento', 100, A),
    ('_gln_origen', 13, A),
    ('_razon_social_origen', 200, A), 
    ('_gln_destino', 13, A),
    ('_razon_social_destino', 200, A), 
    ('_n_remito', 20, A),
    ('_n_factura', 20, A),
    ('_vencimiento', 10, A),
]

# Formato para Errores
ERRORES = [
    ('_c_error', 4, A),                 # c�digo
    ('_d_error', 250, A),               # descripci�n
    ]

             
def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Resultado = self.CodigoTransaccion = ""
            self.Errores = []   # lista de strings para la interfaz
            self.errores = []   # lista de diccionarios (uso interno)
            self.CantPaginas = self.HayError = None
            self.TransaccionPlainWS = []
            self.Traceback = self.Excepcion = ""
            
            if self.client is None:
                raise RuntimeError("Debe llamar a Conectar")

            # llamo a la funci�n (sin reintentos)
            return func(self, *args, **kwargs)

        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            return False
        finally:
            # guardo datos de depuraci�n
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class TrazaMed:
    "Interfaz para el WebService de Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP"
    _public_methods_ = ['SendMedicamentos',
                        'SendCancelacTransacc', 'SendCancelacTransaccParcial',
                        'SendMedicamentosDHSerie',
                        'SendMedicamentosFraccion',
                        'SendConfirmaTransacc', 'SendAlertaTransacc',
                        'GetTransaccionesNoConfirmadas',
                        'GetEnviosPropiosAlertados',
                        'Conectar', 'LeerError', 'LeerTransaccion',
                        'SetUsername', 
                        'SetParametro', 'GetParametro',
                        'GetCodigoTransaccion', 'GetResultado', 'LoadTestXML']
                        
    _public_attrs_ = [
        'Username', 'Password', 
        'CodigoTransaccion', 'Errores', 'Resultado',
        'XmlRequest', 'XmlResponse', 
        'Version', 'InstallDir', 
        'Traceback', 'Excepcion',
        'CantPaginas', 'HayError', 'TransaccionPlainWS',
        ]

    _reg_progid_ = "TrazaMed"
    _reg_clsid_ = "{8472867A-AE6F-487F-8554-C2C896CFFC3E}"

    if TYPELIB:
        _typelib_guid_ = '{F992EB7E-AFBD-41BB-B717-5693D3A2BADB}'
        _typelib_version_ = 1, 4
        _com_interfaces_ = ['ITrazaMed']

    Version = "%s %s %s" % (__version__, HOMO and 'Homologaci�n' or '', 
                            pysimplesoap.client.__version__)

    def __init__(self):
        self.Username = self.Password = None
        self.CodigoTransaccion = self.Errores = self.Resultado = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = ''
        self.client = None
        self.Traceback = self.Excepcion = ""
        self.Log = None
        self.InstallDir = INSTALL_DIR
        self.params = {}

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.errores = ret.get('errores', [])
        self.Errores = ["%s: %s" % (it['_c_error'], it['_d_error'])
                        for it in ret.get('errores', [])]
        self.Resultado = ret.get('resultado')

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None):
        # cliente soap del web service
        try:
            if wrapper:
                Http = set_http_wrapper(wrapper)
                self.Version = TrazaMed.Version + " " + Http._wrapper_version
            proxy_dict = parse_proxy(proxy)
            if HOMO or not wsdl:
                wsdl = WSDL
                location = LOCATION
            if not wsdl.endswith("?wsdl") and wsdl.startswith("http"):
                location = wsdl
                wsdl += "?wsdl"
            elif wsdl.endswith("?wsdl"):
                location = wsdl[:-5]
            if not cache or HOMO:
                # use 'cache' from installation base directory 
                cache = os.path.join(self.InstallDir, 'cache')
            if "--trace" in sys.argv:
                print "Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict)
            self.client = SoapClient(
                wsdl = wsdl,        
                cache = cache,
                proxy = proxy_dict,
                ns="tzmed",
                cacert=cacert,
                soap_ns="soapenv",
                soap_server="jetty",
                trace = "--trace" in sys.argv)
                
            # corrijo ubicaci�n del servidor (localhost:9050 en el WSDL)
            if 'IWebServiceService' in self.client.services:
                ws = self.client.services['IWebServiceService']  # version 1
            else:
                ws = self.client.services['IWebService']         # version 2
            ws['ports']['IWebServicePort']['location'] = location
            
            # Establecer credenciales de seguridad:
            self.client['wsse:Security'] = {
                'wsse:UsernameToken': {
                    'wsse:Username': self.Username,
                    'wsse:Password': self.Password,
                    }
                }
            return True
        except:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            return False

    def SetParametro(self, clave, valor):
        "Establece un par�metro general (usarse en llamadas posteriores)"
        # �til para par�metros de entrada (por ej. VFP9 no soporta m�s de 27)
        self.params[clave] = valor
        return True

    def GetParametro(self, clave):
        "Devuelve un par�metro general (establecido por llamadas anteriores)"
        # �til para par�metros de salida (por ej. campos de TransaccionPlainWS)
        return self.params.get(clave)
        
    @inicializar_y_capturar_excepciones
    def SendMedicamentos(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_documento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None,
                         ):
        "Realiza el registro de una transacci�n de medicamentos. "
        # creo los par�metros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social or None, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_documento': tipo_documento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    }
        # actualizo con par�metros generales:
        params.update(self.params)
        res = self.client.sendMedicamentos(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendMedicamentosFraccion(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_documento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None, cantidad=None,
                         ):
        "Realiza el registro de una transacci�n de medicamentos fraccionados"
        # creo los par�metros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social or None, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_documento': tipo_documento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    'cantidad': cantidad,
                    }
        # actualizo con par�metros generales:
        params.update(self.params)
        res = self.client.sendMedicamentosFraccion(
            arg0=params,                    
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True
        
    @inicializar_y_capturar_excepciones
    def SendMedicamentosDHSerie(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         desde_numero_serial, hasta_numero_serial,
                         id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_documento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None,
                         ):
        "Env�a un lote de medicamentos informando el desde-hasta n�mero de serie"
        # creo los par�metros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'desde_numero_serial': desde_numero_serial, 
                    'hasta_numero_serial': hasta_numero_serial, 
                    'id_obra_social': id_obra_social or None, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_documento': tipo_documento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    }
        # actualizo con par�metros generales:
        params.update(self.params)
        res = self.client.sendMedicamentosDHSerie(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransacc(self, usuario, password, codigo_transaccion):
        " Realiza la cancelaci�n de una transacci�n"
        res = self.client.sendCancelacTransacc(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransaccParcial(self, usuario, password, codigo_transaccion,
                                    gtin_medicamento=None, numero_serial=None):
        " Realiza la cancelaci�n parcial de una transacci�n"
        res = self.client.sendCancelacTransaccParcial(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
            arg3=gtin_medicamento,
            arg4=numero_serial,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendConfirmaTransacc(self, usuario, password, p_ids_transac, f_operacion):
        "Confirma la recepci�n de un medicamento"
        res = self.client.sendConfirmaTransacc(
            arg0=usuario, 
            arg1=password,
            arg2={'p_ids_transac': p_ids_transac, 'f_operacion': f_operacion}, 
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('id_transac_asociada')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def SendAlertaTransacc(self, usuario, password, p_ids_transac_ws):
        "Alerta un medicamento, acci�n contraria a �confirmar la transacci�n�."
        res = self.client.sendAlertaTransacc(
            arg0=usuario, 
            arg1=password,
            arg2=p_ids_transac_ws, 
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('id_transac_asociada')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def GetTransaccionesNoConfirmadas(self, usuario, password, 
                p_id_transaccion_global=None, id_agente_informador=None, 
                id_agente_origen=None, id_agente_destino=None, 
                id_medicamento=None, id_evento=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                n_remito=None, n_factura=None,
                estado=None,
                ):
        "Trae un listado de las transacciones que no est�n confirmadas"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if p_id_transaccion_global is not None:
            kwargs['arg2'] = p_id_transaccion_global
        if id_agente_informador is not None:
            kwargs['arg3'] = id_agente_informador
        if id_agente_origen is not None:
            kwargs['arg4'] = id_agente_origen
        if id_agente_destino is not None: 
            kwargs['arg5'] = id_agente_destino
        if id_medicamento is not None: 
            kwargs['arg6'] = id_medicamento
        if id_evento is not None: 
            kwargs['arg7'] = id_evento
        if fecha_desde_op is not None: 
            kwargs['arg8'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg9'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg10'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg11'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg12'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg13'] = fecha_hasta_v
        if n_remito is not None: 
            kwargs['arg14'] = n_remito
        if n_factura is not None: 
            kwargs['arg15'] = n_factura
        if estado is not None: 
            kwargs['arg16'] = estado

        # llamo al webservice
        res = self.client.getTransaccionesNoConfirmadas(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionPlainWS = [it for it in ret.get('list', [])]
        return True

    def  LeerTransaccion(self):
        "Recorro TransaccionPlainWS devuelto por GetTransaccionesNoConfirmadas"
         # usar GetParametro para consultar el valor retornado por el webservice
        
        if self.TransaccionPlainWS:
            # extraigo el primer item
            self.params = self.TransaccionPlainWS.pop(0)
            return True
        else:
            # limpio los par�metros
            self.params = {}
            return False

    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"
        
        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def GetEnviosPropiosAlertados(self, usuario, password, 
                p_id_transaccion_global=None, id_agente_informador=None, 
                id_agente_origen=None, id_agente_destino=None, 
                id_medicamento=None, id_evento=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                n_remito=None, n_factura=None,
                ):
        "Obtiene las distribuciones y env�os propios que han sido alertados"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if p_id_transaccion_global is not None:
            kwargs['arg2'] = p_id_transaccion_global
        if id_agente_informador is not None:
            kwargs['arg3'] = id_agente_informador
        if id_agente_origen is not None:
            kwargs['arg4'] = id_agente_origen
        if id_agente_destino is not None: 
            kwargs['arg5'] = id_agente_destino
        if id_medicamento is not None: 
            kwargs['arg6'] = id_medicamento
        if id_evento is not None: 
            kwargs['arg7'] = id_evento
        if fecha_desde_op is not None: 
            kwargs['arg8'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg9'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg10'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg11'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg12'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg13'] = fecha_hasta_v
        if n_remito is not None: 
            kwargs['arg14'] = n_remito
        if n_factura is not None: 
            kwargs['arg15'] = n_factura

        # llamo al webservice
        res = self.client.getEnviosPropiosAlertados(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionPlainWS = [it for it in ret.get('list', [])]
        return True

    def SetUsername(self, username):
        "Establezco el nombre de usuario"        
        self.Username = username

    def SetPassword(self, password):
        "Establezco la contrase�a"        
        self.Password = password

    def GetCodigoTransaccion(self):
        "Devuelvo el c�digo de transacci�n"        
        return self.CodigoTransaccion

    def GetResultado(self):
        "Devuelvo el resultado"        
        return self.Resultado

    def LoadTestXML(self, xml_file):
        "Cargar una respuesta predeterminada de pruebas (emulaci�n del ws)"
        # cargo el ejemplo de AFIP (emulando respuesta del webservice)
        from pysimplesoap.transport import DummyTransport as DummyHTTP 
        xml = open(os.path.join(INSTALL_DIR, xml_file)).read()
        self.client.http = DummyHTTP(xml)


def main():
    "Funci�n principal de pruebas (obtener CAE)"
    import os, time, sys
    global WSDL, LOCATION

    DEBUG = '--debug' in sys.argv

    ws = TrazaMed()
    
    ws.Username = 'testwservice'
    ws.Password = 'testwservicepsw'
    
    if '--prod' in sys.argv and not HOMO:
        WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService"
        print "Usando WSDL:", WSDL
        sys.argv.pop(0)

    # Inicializo las variables y estructuras para el archivo de intercambio:
    medicamentos = []
    transacciones = []
    errores = []
    formatos = [('Medicamentos', MEDICAMENTOS, medicamentos), 
                ('Transacciones', TRANSACCIONES, transacciones),
                ('Errores', ERRORES, errores),
               ]

    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato, lista in formatos:
            comienzo = 1
            print "=== %s ===" % msg
            print "|| %-25s || %-12s || %-5s || %-4s || %-10s ||" % (  
                "Nombre", "Tipo", "Long.", "Pos(txt)", "Campo(dbf)")
            claves = []
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                clave_dbf = dar_nombre_campo_dbf(clave, claves)
                claves.append(clave_dbf)
                print "|| %-25s || %-12s || %5d ||   %4d   || %-10s ||" % (
                    clave, tipo, longitud, comienzo, clave_dbf)
                comienzo += longitud
        sys.exit(0)
        
    if '--cargar' in sys.argv:
        if '--dbf' in sys.argv:
            leer_dbf(formatos[:1], {})        
        elif '--json' in sys.argv:
            for formato in formatos[:1]:
                archivo = open(formato[0].lower() + ".json", "r")
                d = json.load(archivo)
                formato[2].extend(d)
                archivo.close()
        else:
            for formato in formatos[:1]:
                archivo = open(formato[0].lower() + ".txt", "r")
                for linea in archivo:
                    d = leer(linea, formato[1])
                    formato[2].append(d)
                archivo.close()
        
    ws.Conectar("", WSDL)
    
    if ws.Excepcion:
        print ws.Excepcion
        print ws.Traceback
        sys.exit(-1)
    
    # Datos de pruebas:
    
    if '--test' in sys.argv:
        medicamentos.append(dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()*10), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_documento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555", 
            nro_asociado="9999999999999",
            cantidad=None, 
            desde_numero_serial=None, hasta_numero_serial=None, 
            codigo_transaccion=None, 
        ))            
    if '--testfraccion' in sys.argv:
        medicamentos.append(dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()*10), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_documento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",
            nro_asociado="9999999999999",
            cantidad=5,
            desde_numero_serial=None, hasta_numero_serial=None, 
            codigo_transaccion=None,
        ))
    if '--testdh' in sys.argv:
        medicamentos.append(dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            desde_numero_serial=int(time.time()*10)-1, 
            hasta_numero_serial=int(time.time()*10)+1, 
            id_obra_social=None, id_evento=134,
            nro_asociado="1234",
            cantidad=None, numero_serial=None,
            codigo_transaccion=None,
        ))

    # Opciones principales:
    
    if '--cancela' in sys.argv:
        ws.SendCancelacTransacc(*sys.argv[sys.argv.index("--cancela")+1:])
    elif '--cancela_parcial' in sys.argv:
        ws.SendCancelacTransaccParcial(*sys.argv[sys.argv.index("--cancela_parcial")+1:])
    elif '--confirma' in sys.argv:
        if '--loadxml' in sys.argv:
            ws.LoadTestXML("trazamed_confirma.xml")  # cargo respuesta
            ok = ws.SendConfirmaTransacc(usuario="pruebasws", password="pruebasws",
                                   p_ids_transac="1", f_operacion="31-12-2013")
            if not ok:
                raise RuntimeError(ws.Excepcion)
        ws.SendConfirmaTransacc(*sys.argv[sys.argv.index("--confirma")+1:])
    elif '--alerta' in sys.argv:
        ws.SendAlertaTransacc(*sys.argv[sys.argv.index("--alerta")+1:])
    elif '--consulta' in sys.argv:
        if '--alertados' in sys.argv:
            ws.GetEnviosPropiosAlertados(
                                *sys.argv[sys.argv.index("--alertados")+1:]
                                )
        else:
            ws.GetTransaccionesNoConfirmadas(
                                *sys.argv[sys.argv.index("--consulta")+1:]
                                #usuario="pruebasws", password="pruebasws", 
                                #p_id_transaccion_global="1234", 
                                #id_agente_informador="1", 
                                #id_agente_origen="1", 
                                #id_agente_destino="1", 
                                #id_medicamento="1", 
                                #id_evento="1", 
                                #fecha_desde_op="01/01/2013", 
                                #fecha_hasta_op="31/12/2013", 
                                #fecha_desde_t="01/01/2013", 
                                #fecha_hasta_t="31/12/2013", 
                                #fecha_desde_v="01/04/2013", 
                                #fecha_hasta_v="30/04/2013", 
                                #n_factura=5, n_remito=6,
                                #estado=1
                                )
        print "CantPaginas", ws.CantPaginas
        print "HayError", ws.HayError
        #print "TransaccionPlainWS", ws.TransaccionPlainWS
        # parametros comunes de salida (columnas de la tabla):
        claves = [k for k, v, l in TRANSACCIONES]
        # extiendo la lista de resultado para el archivo de intercambio:
        transacciones.extend(ws.TransaccionPlainWS)
        # encabezado de la tabla:
        print "||", "||".join(["%s" % clave for clave in claves]), "||"
        # recorro los datos devueltos (TransaccionPlainWS):
        while ws.LeerTransaccion():     
            for clave in claves:
                print "||", ws.GetParametro(clave),         # imprimo cada fila
            print "||"
    else:
        if not medicamentos:
            if len(sys.argv)>16:
                ws.SendMedicamentos(*sys.argv[1:])
            else:
                print "ERROR: no se indicaron todos los par�metros requeridos"
        elif medicamentos:
            try:
                usuario, password = [argv for argv in sys.argv 
                                     if not argv.startswith("--")][-2:]
            except:
                print "ADVERTENCIA: no se indico par�metros usuario y passoword"
                usuario = password = "pruebasws"
            for i, med in enumerate(medicamentos):
                print "Procesando registro", i
                del med['codigo_transaccion']
                if med.get("cantidad"):
                    del med["desde_numero_serial"]
                    del med["hasta_numero_serial"]
                    ws.SendMedicamentosFraccion(usuario, password, **med)
                elif med.get("desde_numero_serial"):
                    del med["cantidad"]
                    del med["numero_serial"]
                    ws.SendMedicamentosDHSerie(usuario, password, **med)
                else:
                    del med["cantidad"]
                    del med["desde_numero_serial"]
                    del med["hasta_numero_serial"]
                    ws.SendMedicamentos(usuario, password, **med)
                med['codigo_transaccion'] = ws.CodigoTransaccion
                errores.extend(ws.errores)
                print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
                    ws.Resultado,
                    ws.CodigoTransaccion,
                    '|'.join(ws.Errores or []),
                    )
        else:
            print "ERROR: no se especificaron medicamentos a informar"
            
    if not medicamentos:
        print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
                ws.Resultado,
                ws.CodigoTransaccion,
                '|'.join(ws.Errores or []),
                )

    if ws.Excepcion:
        print ws.Traceback

    if '--grabar' in sys.argv:
        if '--dbf' in sys.argv:
            guardar_dbf(formatos, True, {})        
        elif '--json' in sys.argv:
            for formato in formatos:
                archivo = open(formato[0].lower() + ".json", "w")
                json.dump(formato[2], archivo, sort_keys=True, indent=4)
                archivo.close()
        else:
            for formato in formatos:
                archivo = open(formato[0].lower() + ".txt", "w")
                for it in formato[2]:
                    archivo.write(escribir(it, formato[1]))
            archivo.close()


# busco el directorio de instalaci�n (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':

    # ajusto el encoding por defecto (si se redirije la salida)
    if sys.stdout.encoding is None:
        import codecs, locale
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
        sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        if TYPELIB: 
            if '--register' in sys.argv:
                tlb = os.path.abspath(os.path.join(INSTALL_DIR, "trazamed.tlb"))
                print "Registering %s" % (tlb,)
                tli=pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif '--unregister' in sys.argv:
                k = TrazaMed
                pythoncom.UnRegisterTypeLib(k._typelib_guid_, 
                                            k._typelib_version_[0], 
                                            k._typelib_version_[1], 
                                            0, 
                                            pythoncom.SYS_WIN32)
                print "Unregistered typelib"
        import win32com.server.register
        win32com.server.register.UseCommandLine(TrazaMed)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([TrazaMed._reg_clsid_])
    else:
        main()