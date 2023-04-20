# -*- coding: utf-8 -*-
from osv import osv
from oorq.oorq import AsyncMode
class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def send_indexada_modcon_activated_email(self, cursor, uid, polissa_id):
        ir_model_data = self.pool.get('ir.model.data')
        account_obj = self.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = self.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_indexada', 'email_activacio_tarifa_indexada'
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        email_account_id = 'info@somenergia.coop'
        if template.get('enforce_from_account', False):
            email_from = template.get('enforce_from_account')[0]
        if not email_from:
            email_from = account_obj.search(cursor, uid, [('email_id', '=', email_account_id)])[0]

        try:
            wiz_send_obj = self.pool.get('poweremail.send.wizard')
            ctx = {
                'active_ids': [polissa_id],
                'active_id': polissa_id,
                'template_id': template_id,
                'src_model': 'giscedata.polissa',
                'src_rec_ids': [polissa_id],
                'from': email_from,
                'state': 'single',
                'priority': '0',
            }

            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            raise e

    def _do_previous_actions_on_activation(self, cursor, uid, mc_id, context=None):
        with AsyncMode('sync') as asmode:
            res = super(GiscedataPolissa, self)._do_previous_actions_on_activation(cursor, uid, mc_id, context)
            modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
            modcon = modcon_obj.read(cursor, uid, mc_id, ['state', 'polissa_id', 'mode_facturacio'])
            if res == 'OK' and modcon['state'] == 'active' and modcon['mode_facturacio'] == 'index':
                self.send_indexada_modcon_activated_email(cursor, uid, modcon['polissa_id'])


