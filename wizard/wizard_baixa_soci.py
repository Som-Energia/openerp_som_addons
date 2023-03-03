# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import logging

class WizardBaixaSoci(osv.osv_memory):

    _name = 'wizard.baixa.soci'
    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info')
    }
    _defaults = {
        'state': 'init'
    }

    def baixa_soci(self, cursor, uid, ids, context=None, send_mail=False):
        soci_obj = self.pool.get('somenergia.soci')
        soci_id = context['active_ids']
        if isinstance(ids, list):
            ids = ids[0]
        wizard = self.browse(cursor, uid, ids, context)

        if not isinstance(soci_id, list):
            soci_id = [soci_id]
        if len(soci_id) != 1:
            raise "Has de seleccionar un sol soci"

        try:
            soci_obj.verifica_baixa_soci(cursor, uid, soci_id[0], context)
        except osv.except_osv as e:
            wizard.write({'state':'error', 'info': e.message})
        else:
            if send_mail:
                self.send_mail(cursor, uid, soci_id[0])
            wizard.write({'state':'ok'})


    def baixa_soci_and_send_mail(self, cursor, uid, ids, context=None):
        self.baixa_soci(cursor, uid, ids, context, send_mail=True)

    def send_mail(self, cursor, uid, soci_id, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        account_obj = self.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = self.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_generationkwh', 'email_baixa_soci'
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        email_account_id = 'info@somenergia.coop'

        if template.get(email_account_id, False):
            email_from = template.get('enforce_from_account')[0]

        if not email_from:
            email_from = account_obj.search(cursor, uid, [('email_id', '=', email_account_id)])[0]

        email_params = dict({
            'email_from': email_from,
            'template_id': template_id
        })

        logger = logging.getLogger('openerp.poweremail')

        try:
            wiz_send_obj = self.pool.get('poweremail.send.wizard')
            ctx = {
                'active_ids': [soci_id],
                'active_id': soci_id,
                'template_id': email_params['template_id'],
                'src_model': 'somenergia.soci',
                'src_rec_ids': [soci_id],
                'from': email_params['email_from'],
                'state': 'single',
                'priority': '0',
            }

            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            logger.info(
                'ERROR sending email to member {soci_id}: {exc}'.format(
                    soci_id=soci_id,
                    exc=e
                )
            )


WizardBaixaSoci()

