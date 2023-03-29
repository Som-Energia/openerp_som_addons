# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import timedelta, date
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
        res = {'k': 4.82, 'd':0.3}
        return res

    def calculate_new_pricelist(self, cursor, uid, polissa, context=None):
        IrModel = self.pool.get('ir.model.data')

        new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_peninsula').id
        if polissa.fiscal_position_id in [19, 25, 33, 34, 38, 39]:
            new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_canaries').id
        elif 'INSULAR' in polissa.llista_preu.name:
            new_pricelist_id = IrModel._get_obj(cursor, uid, 'som_indexada', 'pricelist_indexada_balears').id

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

    def change_to_indexada(self, cursor, uid, ids, context=None):
        '''update data_firma_contracte in polissa
        and data_inici in modcontractual'''
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')

        wizard = self.browse(cursor, uid, ids[0])
        polissa = wizard.polissa_id

        if not context:
            context = {}

        self.validate_polissa_can_indexada(cursor, uid, polissa)
        coefs = self.calculate_k_d_coeficients(cursor, uid)
        new_pricelist_id = self.calculate_new_pricelist(cursor, uid, polissa)

        prev_modcon = polissa.modcontractuals_ids[0]
        modcon_obj.write(cursor, uid, prev_modcon.id, {
            'data_final': date.today(),
        })

        new_modcon_vals = modcon_obj.copy_data(
            cursor, uid, prev_modcon.id
        )[0]
        new_modcon_vals.update({
            'data_inici': date.today() + timedelta(days=1),
            'data_final': date.today() + timedelta(days=365),
            'mode_facturacio': 'index',
            'mode_facturacio_generacio': 'index',
            'llista_preu': new_pricelist_id,
            'coeficient_k': coefs['k'],
            'coeficient_d': coefs['d'],
            'active': True,
            'state': 'pendent',
            'modcontractual_ant': prev_modcon.id,
        })
        new_modcon_id = modcon_obj.create(cursor, uid, new_modcon_vals)

        modcon_obj.write(cursor, uid, prev_modcon.id, {
            'modcontractual_seg': new_modcon_id,
            'state': 'baixa2',
        })

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