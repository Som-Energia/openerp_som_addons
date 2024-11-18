# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataFacturacioFactura(osv.osv):
    """Classe per la factura de comercialitzadora."""
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    # Poweremails hooks
    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        res = True
        if hasattr(super(GiscedataFacturacioFactura, self), 'poweremail_write_callback'):
            res = super(GiscedataFacturacioFactura, self).poweremail_write_callback(
                cursor, uid, ids, vals, context=context
            )
        mail_obj = self.pool.get('poweremail.mailbox')

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        if 'pe_callback_origin_ids' in context:
            for fact_id in ids:
                fact_data = self.read(
                    cursor,
                    uid,
                    fact_id,
                    ['enviat_mail_id', 'number']
                )
                fact_number = fact_data['number']
                if not fact_number:  # Not open invoice
                    continue
                fact_enviat_mail_id = fact_data['enviat_mail_id']
                if fact_enviat_mail_id:  # There is a previous one
                    continue

                new_mail_id = context['pe_callback_origin_ids'].get(fact_id, None)
                if not new_mail_id:  # no new mail
                    continue

                new_mail = mail_obj.browse(cursor, uid, new_mail_id)
                if (new_mail.pem_attachments_ids
                        and new_mail.pem_attachments_ids[0].datas_fname == fact_number + '.pdf'):
                    self.write(cursor, uid, fact_id, {'enviat_mail_id': new_mail_id})

        return res

    _columns = {
        'enviat_mail_id': fields.many2one(
            "poweremail.mailbox",
            "E-Mail factura adjunta",
            readonly=True,
            ondelete="set null"
        ),
    }


GiscedataFacturacioFactura()
