# -*- coding: utf-8 -*-

import json
from osv import osv, fields
from datetime import datetime, date
from tools.translate import _


class GenerationkwhInvestmentSign(osv.osv):

    _name = 'generationkwh.investment'
    _inherit = 'generationkwh.investment'

    def investment_sign_request(self, cursor, uid, gen_ids, context=None):
        if context is None:
            context = {}

        for item_id in gen_ids:
            invest = self.browse(cursor, uid, item_id)
            email = None
            address_id = None
            try:
                address_id = invest.member_id.address[0].id
                email = invest.member_id.address[0].email
            except Exception as e:
                raise osv.except_osv(
                    _('Error!'),
                    _(u"Se necesita una dirección con correo electrónico "
                      u"donde enviar el documento a firmar.")
                )
            else:
                acc_inv_obj = self.pool.get('account.invoice')
                conf_obj = self.pool.get('res.config')
                imd_obj = self.pool.get('ir.model.data')
                attach_obj = self.pool.get('ir.attachment')
                add_obj = self.pool.get('res.partner.address')
                pro_obj = self.pool.get('giscedata.signatura.process')

                max_signable_documents = int(conf_obj.get(
                    cursor, uid, 'signature_signaturit_max_signable_documents', '2'))

                generation_report_id = imd_obj.get_object_reference(
                    cursor, uid, 'som_inversions', 'report_generationkwh_doc'
                )[1]

                data = json.dumps({
                    'callback_method': 'generationkwh_signed',
                    'gen_id': item_id
                })

                subject = 'Firma del contracte GenerationKWh amb identificador ' + self.read(cursor, uid, item_id, ['name'])['name']
                files = []

                acc_inv_id = acc_inv_obj.search(cursor, uid, [("origin", "=", invest.name)])

                if len(acc_inv_id) == 0:
                    raise osv.except_osv(
                        _('Error!'),
                        _(u"No hi ha cap factura per a aquest préstec de generation!")
                    )

                doc_file = (0, 0, {
                    'model': 'account.invoice,{}'.format(acc_inv_id[0]),
                    'report_id': generation_report_id,
                    'category_id': 0, #TODO: no hi ha cateogries, s'han de fer?
                })
                files.append(doc_file)

                recipients = [
                    (0, 0, {
                        'partner_address_id': address_id,
                        'name': invest.member_id.name,
                        'email': email
                    })
                ]

                values = {
                    'subject': subject,  # Titulo del correo electronico
                    'delivery_type': 'email',  # Metodo de envio
                    'recipients': recipients,  # Personas que deberan firmar
                    'reminders': 0,
                    'type': 'advanced',
                    'data': data,
                    'all_signed': False,  # Ver esquema
                    'files': files  # Documentos
                }

                process_id = pro_obj.create(cursor, uid, values, context=context)
                pro_obj.start(cursor, uid, [process_id], context=context)

        return 0

GenerationkwhInvestmentSign()
