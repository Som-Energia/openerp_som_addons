# -*- coding: utf-8 -*-
import base64
import csv
import StringIO
import re
from tqdm import tqdm
import pandas as pd

from osv import osv, fields
from datetime import datetime, timedelta, date
from tools.translate import _

class WizardExportTugestoInvoices(osv.osv_memory):
    _name = 'wizard.export.tugesto.invoices'

    def tugesto_invoices_export(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context)
        fact_ids = context['active_ids']

        headers = ['identificador_expediente','Id_tipo','importe_pagare','tipo_deudor','nif_cif',
            'razon_social','nombre','apellidos','direccion','provincia','poblacion','pais',
            'poblacion_pais','codigo_postal','telefono','movil','email','emails_adicionales',
            'numero_factura','fecha_factura','importe_factura','partner_lang']      

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        res_partner_obj = self.pool.get('res.partner')
        imd_obj = self.pool.get('ir.model.data')
        default_process = imd_obj.get_object_reference(cursor, uid,
                'account_invoice_pending',
                'default_pending_state_process')[1]

        llistat = []

        for fact_id in fact_ids:
            factura = fact_obj.browse(cursor, uid, fact_id)
            partner = factura.partner_id
            nom_sencer = factura.partner_id.name
            identificador_expediente = "{}-{}".format(partner.vat,datetime.strftime(date.today(),'%Y-%m-%d'))
            Id_tipo = 2 # Expediente Prejudicial
            importe_pagare = 0.0 
            tipo_deudor = 2 if factura.pending_state.process_id.id == default_process else 1 # 'Comunidad de Bienes' ha de ser 3

            nif_cif = partner.vat.replace('ES','')
            try:
                nif_cif = '{}{}'.format(re.findall('^[XYZ]\d{7,8}[A-Z]$', nif_cif)[0],'*')
            except IndexError:
                pass

            razon_social = partner.name if factura.pending_state.process_id.id == default_process else ''
            nombre = '' if factura.pending_state.process_id.id == default_process else res_partner_obj.separa_cognoms(cursor,uid, partner.name)['nom']
            apellidos = '' if factura.pending_state.process_id.id == default_process else res_partner_obj.separa_cognoms(cursor,uid, partner.name)['cognoms'] 
            
            direccion = ''
            addr_objs = [ad for ad in partner.address if ad.type == 'default']
            aux_addr = None
            if addr_objs:
                aux_addr = addr_objs[0]
            else:
                aux_addr = partner.address[0]

            direccion = '{}. {} {}'.format(aux_addr.street,aux_addr.zip,aux_addr.city)
            provincia = aux_addr.id_municipi.state.code
            poblacion = aux_addr.id_municipi.ine
            pais = 9 # Codi propi de Tugesto per a Espanya
            poblacion_pais =  aux_addr.id_municipi.name
            codigo_postal = aux_addr.zip 
            telefono = aux_addr.phone
            movil = aux_addr.mobile
            email = aux_addr.email
            emails_adicionales = ''
            numero_factura = factura.number
            fecha_factura = datetime.strftime(datetime.strptime(factura.date_invoice,'%Y-%m-%d'),'%d-%m-%Y') #forcem a format espanyol
            importe_factura = factura.residual
            idioma_comunicacion = partner.lang

            llistat.append({
                'identificador_expediente': identificador_expediente,
                'Id_tipo': Id_tipo,
                'importe_pagare': importe_pagare,
                'tipo_deudor': tipo_deudor,
                'nif_cif':nif_cif,
                'razon_social':razon_social,
                'nombre':nombre,
                'apellidos':apellidos,
                'direccion':direccion,
                'provincia':provincia,
                'poblacion':poblacion,
                'pais':pais,
                'poblacion_pais':poblacion_pais,
                'codigo_postal':codigo_postal,
                'telefono':telefono,
                'movil':movil,
                'email':email,
                'emails_adicionales':emails_adicionales,
                'numero_factura':numero_factura,
                'fecha_factura':fecha_factura,
                'importe_factura':importe_factura,
                'idioma_comunicacion': idioma_comunicacion,}
            )

        df = pd.DataFrame(llistat)
        filename = 'Plantilla Entrada.xlsx'
        output = StringIO.StringIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Expedientes')
        workbook = writer.book
        header_format = workbook.add_format({'bold': True})
        worksheet = writer.sheets['Expedientes']
        for col_num, value in enumerate(headers):
            worksheet.write(0, col_num, value, header_format)
        writer.save()

        output.close()
        mfile = base64.b64encode(output.getvalue())

        self.write(cursor, uid, ids, {
                'state': 'done',
                'file_name': filename,
                'file': mfile
            })


    _columns = {
        'name': fields.char('Nom fitxer', size=32),
        'state': fields.char('State', size=16),
        'file_name': fields.binary('Fitxer'),
    }
    _defaults = {
        'state': lambda *a: 'init',
    }

WizardExportTugestoInvoices()
