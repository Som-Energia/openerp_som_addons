# -*- coding: utf-8 -*-
import netsvc
import logging
from tqdm import tqdm
from datetime import datetime, timedelta
from osv import osv, fields
from addons import get_module_resource


logger = logging.getLogger('openerp' + __name__)


class GiscedataFacturacioFactura(osv.osv):
    """Classe per la factura de comercialitzadora."""
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        res, x = super(GiscedataFacturacioFactura, self).copy_data(
            cr, uid, id, default, context
        )
        res.update({
            'enviat_mail_id': False,
            'enviat': False,
            'enviat_data': False,
            'enviat_carpeta': False,
        })
        return res, x

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

        if 'folder' in vals and vals['folder'] == 'sent' and 'pe_callback_origin_ids' in context:
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

                new_mail = mail_obj.simple_browse(cursor, uid, new_mail_id)
                if (new_mail.pem_attachments_ids
                        and new_mail.pem_attachments_ids[0].datas_fname == fact_number + '.pdf'):
                    self.write(cursor, uid, fact_id, {'enviat_mail_id': new_mail_id})

        return res

    def store_unsent_pdf_invoices(self, cursor, uid, context=None):
        if context is None:
            context = {}
        context.update({'save_pdf_in_invoice_attachments': True})

        conf_obj = self.pool.get("res.config")
        unsent_store_days = int(conf_obj.get(cursor, uid, "factura_pdf_unsent_store_days", 60))
        date_search = datetime.today() - timedelta(days=unsent_store_days)

        query_file = get_module_resource(
            'giscedata_facturacio_comer_som', 'sql', "query_fact_to_pdf_store.sql")
        query = open(query_file).read()

        cursor.execute(query, (date_search.strftime('%Y-%m-%d'), ))
        unstored_fact_ids = [x[0] for x in cursor.fetchall()]

        error_ids = []
        for fact_id in tqdm(unstored_fact_ids, "Printing and storing invoices"):
            try:
                report = netsvc.service_exist("report.giscedata.facturacio.factura")
                values = {
                    "model": "giscedata.facturacio.factura",
                    "id": [fact_id],
                    "report_type": "pdf",
                }
                report.create(cursor, uid, [fact_id], values, context)[0]
                logger.debug("Invoice %s printed and stored", fact_id)
            except Exception:
                logger.warning("Invoice %s FAILED", fact_id)
                error_ids.append(fact_id)

        total_successful = len(unstored_fact_ids) - len(error_ids)
        return total_successful, error_ids

    _columns = {
        'enviat_mail_id': fields.many2one(
            "poweremail.mailbox",
            "E-Mail factura adjunta",
            readonly=True,
            ondelete="set null"
        ),
    }


GiscedataFacturacioFactura()
