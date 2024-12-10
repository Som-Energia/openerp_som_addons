# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime


class WizardLoadServeiGenRecordsFromFile(osv.osv_memory):
    _name = 'wizard.load.servei.gen.records.from.file'
    _inherit = 'wizard.load.servei.gen.records.from.file'

    def get_polissa_from_record_data(self, cursor, uid, cups_name, data, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')

        ctx = context.copy()
        ctx.update({'active_test': False})
        polissa_id = pol_obj.search(cursor, uid, [
            ('cups.name', '=', cups_name),
        ], order='id desc', context=ctx)

        return polissa_id

    def get_aux_dict_from_row(self, cursor, uid, row, tipus='contracte', context=None):
        if context is None:
            context = {}
        today = datetime.now().strftime('%Y-%m-%d')
        aux_dict = {
            'data_inici': False,
            'data_sortida': row[2],
            'data_incorporacio': today,
            'percentatge': float(row[3].replace(',', '.')),
        }

        if tipus == 'empresa':
            aux_dict.update({
                'cups': row[1],
            })
        else:
            aux_dict.update({
                'nif': row[0],
            })
        return aux_dict


WizardLoadServeiGenRecordsFromFile()
