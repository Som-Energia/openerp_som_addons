# -*- coding: utf-8 -*-
import base64
import csv
import StringIO
import re
from tqdm import tqdm
import pandas as pd
import json

from osv import osv, fields
from datetime import datetime, timedelta, date
from tools.translate import _

class WizardExportTugestoInvoices(osv.osv_memory):
    _name = 'wizard.export.tugesto.invoices'

    def tugesto_invoices_export(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context)
        fact_ids = context['active_ids']
        if not fact_ids:
            raise osv.except_osv(_('Error'), _("No s'ha seleccionat cap factura"))
        
        if not fact_ids:
            raise osv.except_osv(_('Error'), _("No s'ha seleccionat cap factura"))

        headers = ['identificador_expediente','Id_tipo','importe_pagare','tipo_deudor','nif_cif',
            'razon_social','nombre','apellidos','direccion','provincia','poblacion','pais',
            'poblacion_pais','codigo_postal','telefono','movil','email','emails_adicionales',
            'numero_factura','fecha_factura','importe_factura','idioma_comunicacion']      

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
            #nom_sencer = factura.partner_id.name
            identificador_expediente = "{}-{}".format(partner.vat,datetime.strftime(date.today(),'%Y-%m-%d'))
            Id_tipo = 2 # Expediente Prejudicial
            importe_pagare = 0.0 

            tipo_deudor = 2 if factura.pending_state.process_id.id == default_process else 1 # 'Comunidad de Bienes' ha de ser 3

            nif_cif = partner.vat.replace('ES','') if partner.vat else ''
            try:
                #trantament pels NIE
                nif_cif = '{}{}'.format(re.findall('^[XYZ]\d{7,8}[A-Z]$', nif_cif)[0],'*')
            except IndexError:
                pass

            razon_social = partner.name if factura.pending_state.process_id.id == default_process else ''
            nombre = '' if factura.pending_state.process_id.id == default_process else res_partner_obj.separa_cognoms(cursor,uid, partner.name)['nom']
            apellidos = '' if factura.pending_state.process_id.id == default_process else res_partner_obj.separa_cognoms(cursor,uid, partner.name)['cognoms'] 
            
            direccion = ''

            if factura.polissa_id.notificacio == 'titular':
                aux_addr = factura.polissa_id.direccio_notificacio 
            else:
                addr_objs = [ad for ad in partner.address if ad.type == 'default'] 
                aux_addr = addr_objs[0] if addr_objs else partner.address[0]

            direccion = aux_addr.street or ''
            provincia = aux_addr.id_municipi.state.code if aux_addr.id_municipi.state else ''
            poblacion = aux_addr.id_municipi.ine if aux_addr.id_municipi else ''
            pais = 9 # Codi propi de Tugesto per a 'Espanya'
            poblacion_pais =  aux_addr.id_municipi.name
            codigo_postal = aux_addr.zip or ''
            telefono = aux_addr.phone or ''
            movil = aux_addr.mobile or ''
            email = aux_addr.email or ''
            emails_adicionales = ''
            numero_factura = factura.number
            fecha_factura = datetime.strftime(datetime.strptime(factura.date_invoice,'%Y-%m-%d'),'%d-%m-%Y') #forcem a format espanyol
            importe_factura = factura.residual
            idioma_comunicacion = partner.lang or 'ca_ES'

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
                'idioma_comunicacion': idioma_comunicacion}
            )

        df = pd.DataFrame(llistat, columns=headers)
        filename = 'Plantilla Entrada.xlsx'
        output = StringIO.StringIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Expedientes', index=None)
        workbook = writer.book
        writer.save()
        mfile = base64.b64encode(output.getvalue())
        output.close()

        self.write(cursor, uid, ids, {
                'state': 'pending',
                'file_name': filename,
                'file_bin': mfile,
                'info': u"Un cop hagis verificat el llistat, pots prémer el botó per moure les factures cap al següent estat pendent.",
                'fact_ids': context.get('active_ids',[])
            })

    def tugesto_invoices_update_pending_state(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context)
        fact_ids = wizard.fact_ids
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        info = u'Hem passat al següent estat pendent {} factures'.format(len(fact_ids))
        try:
            import pudb;pu.db
            fact_obj.go_on_pending(cursor, uid, fact_ids)
        except Exception as ex:
            info = u"Hi ha hagut un error en intentar passar de estat {} factures. Aquest és l'error: {}.".format(len(fact_ids), ex.message)

        self.write(cursor, uid, ids, {
                'state': 'done',
                'info': info,
            })

    def tugesto_list_invoices(self, cursor, uid, ids, context=None):

        wizard = self.browse(cursor, uid, ids[0], context)
        fact_ids = list(wizard.fact_ids) #json.loads(wizard.fact_ids)
        return {
            'domain': "[('id','in', %s)]" % str(fact_ids),
            'name': 'Factures',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'giscedata.facturacio.factura',
            'type': 'ir.actions.act_window'
        }

    _columns = {
        'file_name': fields.char('Nom fitxer', size=32),
        'state': fields.char('State', size=16),
        'file_bin': fields.binary('Fitxer'),
        'info': fields.text(u'Informació',readonly=True),
        'fact_ids': fields.text(),
    }
    _defaults = {
        'state': lambda *a: 'init',
        'info': '',
    }

WizardExportTugestoInvoices()
