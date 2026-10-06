# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import logging

class WizardBaixaSoci(osv.osv_memory):

    _name = 'wizard.baixa.soci'

    _columns = {
        'state': fields.selection([
            ('init', 'Inici'),
            ('checklist', 'Verificació'),
            ('done', 'Resultat'),
        ], string='Estat'),
        'error': fields.text('Error'),
        'info': fields.text('Info'),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'bank_account_id': fields.many2one(
            'res.partner.bank', 'Compte bancari per devolució', required=True,
        ),
        'skip_pending_check': fields.boolean('Salta la comprovació de factures pendents'),
        'skip_sponsored_check': fields.boolean('Desvincula pòlisses apadrinades'),
    }

    def _get_default_partner_id(self, cursor, uid, context=None):
        soci_id = self._get_soci_from_context(context)
        soci_obj = self.pool.get('somenergia.soci')
        soci = soci_obj.read(cursor, uid, soci_id[0], ['partner_id'])
        return soci['partner_id'][0]

    _defaults = {
        'state': lambda *a: 'init',
        'error': lambda *a: '',
        'partner_id': _get_default_partner_id,
    }

    def verify(self, cursor, uid, ids, context=None):
        soci_obj = self.pool.get('somenergia.soci')
        soci_id = self._get_soci_from_context(context)
        if isinstance(ids, list):
            ids = ids[0]

        wizard = self.browse(cursor, uid, ids, context)

        # We enforce skip_pending_check=False during verification to show all issues
        reasons = soci_obj.get_baixa_blocking_reasons(cursor, uid, soci_id[0], context={
            'skip_pending_check': False,
            'skip_sponsored_check': False
        })

        result_text = _("##### Tot correcte.\nEs pot procedir a la baixa.")
        if reasons:
            result_text = _("##### Hi ha motius que impedeixen la baixa:\n* ") + "\n* ".join(reasons)

        wizard.write({'state': 'checklist', 'info': result_text})

    def baixa_soci(self, cursor, uid, ids, context=None, send_mail=False):
        soci_obj = self.pool.get('somenergia.soci')
        soci_id = self._get_soci_from_context(context)
        if isinstance(ids, list):
            ids = ids[0]

        wizard = self.browse(cursor, uid, ids, context)
        try:
            if wizard.skip_pending_check:
                context['skip_pending_check'] = True
            if wizard.skip_sponsored_check:
                context['skip_sponsored_check'] = True
            soci_obj.do_baixa_soci(cursor, uid, soci_id[0], wizard.bank_account_id.id, context)
        except osv.except_osv as e:
            wizard.write({'info': e.message, 'error': "No es pot donar de baixa"})
        else:
            if send_mail:
                self.send_mail(cursor, uid, soci_id[0])
            wizard.write({'state':'done'})

    def _get_soci_from_context(self, context):
        soci_id = context['active_ids']
        if not isinstance(soci_id, list):
            soci_id = [soci_id]
        if len(soci_id) != 1:
            raise osv.except_osv("Error", "Has de seleccionar un sol soci")
        return soci_id

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
