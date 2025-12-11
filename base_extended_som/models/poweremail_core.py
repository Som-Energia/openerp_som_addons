# -*- coding: utf-8 -*-
import json
from osv import osv
import netsvc


class poweremail_core_accounts(osv.osv):
    _inherit = "poweremail.core_accounts"

    def send_mail(self, cr, uid, ids,
                  addresses, subject='', body=None, payload=None, context=None):
        context = context or {}
        logger = netsvc.Logger()

        template_obj = self.pool.get('poweremail.templates')
        mail_obj = self.pool.get('poweremail.mailbox')
        category_obj = self.pool.get('poweremail.sendgrid.category')

        try:
            mail_id = context.get('poweremail_id')
            template_id = mail_obj.read(
                cr, uid, mail_id, ['template_id'], context=context)['template_id'][0]
            category_ids = template_obj.read(
                cr, uid, template_id,
                ['sendgrid_category_ids'], context=context
            )['sendgrid_category_ids']

            if category_ids:
                categories = category_obj.browse(
                    cr, uid, category_ids, context=context)
                extra_headers = context.get('headers', {})
                extra_headers['X-SMTPAPI'] = json.dumps({
                    'category': [category.name for category in categories]
                })
                context['headers'] = extra_headers
        except Exception as error:
            logger.notifyChannel(
                "Power Email",
                netsvc.LOG_WARNING,
                "Error adding SendGrid categories to email: {}".format(error)
            )

        return super(poweremail_core_accounts, self).send_mail(
            cr, uid, ids, addresses, subject, body, payload, context)


poweremail_core_accounts()
