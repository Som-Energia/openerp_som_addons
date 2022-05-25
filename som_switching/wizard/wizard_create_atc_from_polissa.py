# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

class WizardCreateAtc(osv.osv_memory):

    _inherit = "wizard.create.atc.from.polissa"

    def onchange_section(self, cursor, uid, ids, section_id):
        res = False
        section_obj = self.pool.get('crm.case.section')
        seccio = section_obj.read(cursor, uid, section_id, ['code'])['code']
        if seccio:
            mostrar_tag = True if seccio == 'ATCF' else False
        return {'value': {'mostrar_tag': mostrar_tag},
                'domain': {},
                'warning': {},
                }

    _columns = {
        'tag': fields.many2one('giscedata.atc.tag', "Etiqueta"),
        'mostrar_tag': fields.boolean(u'Mostrar_tag'),
    }
    _defaults = {
        'mostrar_tag': lambda *a: False,
    }
WizardCreateAtc()