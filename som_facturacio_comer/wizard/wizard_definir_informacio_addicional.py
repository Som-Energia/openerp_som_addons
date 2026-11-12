# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime
from osv import osv


class WizardDefinirInformacioAddicional(osv.osv_memory):
    _name = "wizard.definir.informacio.addicional"
    _inherit = "wizard.definir.informacio.addicional"

    def definir_informacio_addicional(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        fact_ids = context.get('active_ids', False)
        info_add_wizard = self.read(cursor, uid, ids, ['comment'])[0]['comment']

        today = datetime.today().strftime('%d/%m/%Y')
        if info_add_wizard:
            info_add_wizard = '{}: {}'.format(today, info_add_wizard)

        for dades_fact in fact_obj.read(cursor, uid, fact_ids, ['comment'], context=context):
            if dades_fact['comment'] and info_add_wizard:
                info_add = info_add_wizard + '\n' + dades_fact['comment']
            else:
                info_add = info_add_wizard

            fact_obj.write(cursor, uid, dades_fact['id'], {
                'comment': info_add
            }, context=context)

        self.write(cursor, uid, ids, {
            'state': 'end',
            'description': 'Información adiconal actualitzada'
        }, context=context)


WizardDefinirInformacioAddicional()
