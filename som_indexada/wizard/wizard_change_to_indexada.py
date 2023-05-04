# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import timedelta, date
from oorq.oorq import AsyncMode
from som_indexada.exceptions import indexada_exceptions


TARIFA_CODIS_INDEXADA = {
    "2.0TD": {
        "peninsula": "pricelist_indexada_20td_peninsula",
        "canaries": "pricelist_indexada_20td_canaries",
        "balears": "pricelist_indexada_20td_balears",
    },
    "3.0TD": {
        "peninsula": "pricelist_indexada_30td_peninsula",
        "canaries": "pricelist_indexada_30td_canaries",
        "balears": "pricelist_indexada_30td_balears",
    },
    "6.1TD": {
        "peninsula": "pricelist_indexada_61td_peninsula",
        "canaries": "pricelist_indexada_61td_canaries",
        "balears": "pricelist_indexada_61td_balears",
    }
}

TARIFA_CODIS_PERIODES = {
    "2.0TD": {
        "peninsula": "pricelist_periodes_20td_peninsula", # id 101
        "canaries": "pricelist_periodes_20td_insular", # id 120
        "balears": "pricelist_periodes_20td_insular",
    },
    "3.0TD": {
        "peninsula": "pricelist_periodes_30td_peninsula", # id 102
        "canaries": "pricelist_periodes_30td_insular", # id 121
        "balears": "pricelist_periodes_30td_insular",
    },
    "6.1TD": {
        "peninsula": "pricelist_periodes_61td_peninsula", # id 103
        "canaries": "pricelist_periodes_61td_insular", # id 122
        "balears": "pricelist_periodes_61td_insular",
    }
}

CHANGE_AUX_VALUES = {
    "from_index_to_period": {
        "comments": "periodes",
        "invoicing_type": "atr",
    },
    "from_period_to_index": {
        "comments": "indexada",
        "invoicing_type": "index",
    },
}

FISCAL_POSITIONS_CANARIES = [19, 25, 33, 34, 38, 39]

class WizardChangeToIndexada(osv.osv_memory):

    _name = 'wizard.change.to.indexada'

    def _default_polissa_id(self, cursor, uid, context=None):
        '''Llegim la pólissa'''
        polissa_id = False
        if context:
            polissa_id = context.get('active_id', False)
        return polissa_id

    def _default_change_type(self, cursor, uid, context=None):
        '''Llegim el tipus de canvi'''
        change_type = False
        if context:
            change_type = context.get('change_type', False)
        return change_type

    def calculate_k_d_coeficients(self, cursor, uid, context=None):
        # k and d come from pricelist
        res = {}
        return res

    def calculate_new_pricelist(self, cursor, uid, polissa, change_type, context=None):
        IrModel = self.pool.get('ir.model.data')
        tarifa_codi = polissa.tarifa_codi

        # Choose price list dict
        dict_tarifa_codis = TARIFA_CODIS_PERIODES
        if change_type == "from_period_to_index":
            dict_tarifa_codis = TARIFA_CODIS_INDEXADA

        if tarifa_codi not in dict_tarifa_codis:
            raise Exception("no exists tarifa")

        # TODO no basar-nos amb el nom???
        if polissa.fiscal_position_id in FISCAL_POSITIONS_CANARIES:
            location = "canaries"
        elif 'INSULAR' in polissa.llista_preu.name or 'balears' in polissa.llista_preu.name:
            location = "balears"
        else:
            location = "peninsula"

        new_pricelist_id = IrModel._get_obj(
            cursor,
            uid,
            'som_indexada',
            dict_tarifa_codis[tarifa_codi][location],
        ).id

        return new_pricelist_id

    def validate_polissa_can_change(self, cursor, uid, polissa, change_type, context=None):
        sw_obj = self.pool.get('giscedata.switching')
        if polissa.state != 'activa':
            raise indexada_exceptions.PolissaNotActive(polissa.name)
        prev_modcon = polissa.modcontractuals_ids[0]
        if prev_modcon.state == 'pendent':
            raise indexada_exceptions.PolissaModconPending(polissa.name)
        if change_type == "from_period_to_index" and polissa.mode_facturacio == 'index':
            raise indexada_exceptions.PolissaAlreadyIndexed(polissa.name)
        if change_type == "from_index_to_period" and polissa.mode_facturacio == 'atr':
            raise indexada_exceptions.PolissaAlreadyPeriod(polissa.name)

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
        change_type = wizard.change_type
        import pudb; pu.db
        if not context:
            context = {}

        self.validate_polissa_can_change(cursor, uid, polissa, change_type)
        coefs = self.calculate_k_d_coeficients(cursor, uid) if change_type == 'from_period_to_index' else None
        new_pricelist_id = self.calculate_new_pricelist(cursor, uid, polissa, change_type)
        new_pricelist = pricelist_obj.browse(cursor, uid, new_pricelist_id, context={'prefetch': False})

        prev_modcon = polissa.modcontractuals_ids[0]
        modcon_obj.write(cursor, uid, prev_modcon.id, {
            'data_final': date.today(),
        })

        new_modcon_vals = modcon_obj.copy_data(
            cursor, uid, prev_modcon.id
        )[0]
        new_observacions = (
            u'* Modcon canvi a {}:\n '
            u'Nova tarifa comer: {}'
        ).format(CHANGE_AUX_VALUES[change_type]['comments'], new_pricelist.name)
        new_modcon_vals.update({
            'data_inici': date.today() + timedelta(days=1),
            'data_final': date.today() + timedelta(days=365),
            'mode_facturacio': CHANGE_AUX_VALUES[change_type]['invoicing_type'],
            'mode_facturacio_generacio': CHANGE_AUX_VALUES[change_type]['invoicing_type'],
            'llista_preu': new_pricelist_id,
            'coeficient_k': False,
            'coeficient_d': False,
            'active': True,
            'state': 'pendent',
            'modcontractual_ant': prev_modcon.id,
            'name': str(int(prev_modcon.name) + 1),
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
        'change_type': fields.selection(
            [
                ('from_index_to_period', 'From index to period'),
                ('from_period_to_index', 'From period to index'),
            ],
            'Change type',
            required=True,
        ),
        'polissa_id': fields.many2one(
            'giscedata.polissa', 'Contracte', required=True
        ),
    }

    _defaults = {
        'polissa_id': _default_polissa_id,
        'change_type': _default_change_type,
        'state': lambda *a: 'init',
    }

WizardChangeToIndexada()