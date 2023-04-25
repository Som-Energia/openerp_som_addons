# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import timedelta, date
from oorq.oorq import AsyncMode
from som_indexada.exceptions import indexada_exceptions

class WizardChangeToIndexada(osv.osv_memory):

    _name = 'wizard.change.to.indexada'

    def default_polissa_id(self, cursor, uid, context=None):
        '''Llegim la pólissa'''
        polissa_id = False
        if context:
            polissa_id = context.get('active_id', False)

        return polissa_id

    def calculate_k_d_coeficients(self, cursor, uid, context=None):
        # k and d come from pricelist
        res = {}
        return res

    def calculate_new_pricelist(self, cursor, uid, polissa, context=None):
        IrModel = self.pool.get('ir.model.data')
        #TODO TDVE?
        if polissa.tarifa_codi == "2.0TD":
            new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_20td_peninsula').id
            if polissa.fiscal_position_id in [19, 25, 33, 34, 38, 39]:
                new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_20td_canaries').id
            elif 'INSULAR' in polissa.llista_preu.name:
                new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_20td_balears').id
        elif polissa.tarifa_codi == "3.0TD":
            new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_30td_peninsula').id
            if polissa.fiscal_position_id in [19, 25, 33, 34, 38, 39]:
                new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_30td_canaries').id
            elif 'INSULAR' in polissa.llista_preu.name:
                new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_30td_balears').id
        elif polissa.tarifa_codi == "6.1TD":
            new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_61td_peninsula').id
            if polissa.fiscal_position_id in [19, 25, 33, 34, 38, 39]:
                new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_61td_canaries').id
            elif 'INSULAR' in polissa.llista_preu.name:
                new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_61td_balears').id

        return new_pricelist_id

    def validate_polissa_can_indexada(self, cursor, uid, polissa, context=None):
        sw_obj = self.pool.get('giscedata.switching')
        if polissa.state != 'activa':
            raise indexada_exceptions.PolissaNotActive(polissa.name)
        prev_modcon = polissa.modcontractuals_ids[0]
        if prev_modcon.state == 'pendent':
            raise indexada_exceptions.PolissaModconPending(polissa.name)

        if polissa.mode_facturacio == 'index':
            raise indexada_exceptions.PolissaAlreadyIndexed(polissa.name)

        res = sw_obj.search(cursor, uid, [
                ('polissa_ref_id', '=', polissa.id),
                ('state', 'in', ['open', 'draft', 'pending']),
                ('proces_id.name', '!=', 'R1'),
            ])

        if res:
            raise indexada_exceptions.PolissaSimultaneousATR(polissa.name)

    def send_indexada_modcon_created_email(self, cursor, uid, polissa):
        ir_model_data = self.pool.get('ir.model.data')
        account_obj = self.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = self.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_indexada', 'email_canvi_tarifa_a_indexada'
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
                'active_ids': [polissa.id],
                'active_id': polissa.id,
                'template_id': template_id,
                'src_model': 'giscedata.polissa',
                'src_rec_ids': [polissa.id],
                'from': email_from,
                'state': 'single',
                'priority': '0',
            }

            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            raise indexada_exceptions.FailSendEmail(polissa.name)


    def change_to_indexada(self, cursor, uid, ids, context=None):
        '''update data_firma_contracte in polissa
        and data_inici in modcontractual'''
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
        pricelist_obj = self.pool.get('product.pricelist')

        wizard = self.browse(cursor, uid, ids[0])
        polissa = wizard.polissa_id

        if not context:
            context = {}

        self.validate_polissa_can_indexada(cursor, uid, polissa)
        coefs = self.calculate_k_d_coeficients(cursor, uid)
        new_pricelist_id = self.calculate_new_pricelist(cursor, uid, polissa)
        new_pricelist = pricelist_obj.browse(cursor, uid, new_pricelist_id, context={'prefetch': False})

        prev_modcon = polissa.modcontractuals_ids[0]
        modcon_obj.write(cursor, uid, prev_modcon.id, {
            'data_final': date.today(),
        })

        new_modcon_vals = modcon_obj.copy_data(
            cursor, uid, prev_modcon.id
        )[0]
        new_observacions = (
            u'* Modcon canvi a indexada:\n '
            u'Nova tarifa comer: {0}'
        ).format(new_pricelist.name)
        new_modcon_vals.update({
            'data_inici': date.today() + timedelta(days=1),
            'data_final': date.today() + timedelta(days=365),
            'mode_facturacio': 'index',
            'mode_facturacio_generacio': 'index',
            'llista_preu': new_pricelist_id,
            'coeficient_k': False,
            'coeficient_d': False,
            'active': True,
            'state': 'pendent',
            'modcontractual_ant': prev_modcon.id,
            'name': str(int(prev_modcon.name)+1),
            'observacions': new_observacions,
        })
        if coefs:
            new_modcon_vals.update({
            'coeficient_k': coefs['k'],
            'coeficient_d': coefs['d'],
            })
        with AsyncMode('sync') as asmode:
            new_modcon_id = modcon_obj.create(cursor, uid, new_modcon_vals)

            modcon_obj.write(cursor, uid, prev_modcon.id, {
                'modcontractual_seg': new_modcon_id,
                'state': 'baixa2',
            })
            self.send_indexada_modcon_created_email(cursor, uid, polissa)

        wizard.write({'state': 'end'})
        return new_modcon_id

    _columns = {
        'state': fields.selection([('init', 'Init'),
                                   ('end', 'End')], 'State'),
        'polissa_id': fields.many2one(
            'giscedata.polissa', 'Contracte', required=True
        ),
    }

    _defaults = {
        'polissa_id': default_polissa_id,
        'state': lambda *a: 'init',
    }

WizardChangeToIndexada()