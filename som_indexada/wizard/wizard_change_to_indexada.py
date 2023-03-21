# -*- coding: utf-8 -*-
from osv import osv, fields

class WizardChangeToIndexada(osv.osv_memory):

    _name = 'wizard.change.to.indexada'

    def default_polissa_id(self, cursor, uid, context=None):
        '''Llegim la pólissa'''
        polissa_id = False
        if context:
            polissa_id = context.get('active_id', False)

        return polissa_id

    def change_to_indexada(self, cursor, uid, ids, context=None):
        '''update data_firma_contracte in polissa
        and data_inici in modcontractual'''

        polissa_obj = self.pool.get('giscedata.polissa')
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
        wizard = self.browse(cursor, uid, ids[0])
        polissa = wizard.polissa_id

        if not context:
            context = {}

        wizard.write({'state': 'end'})

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