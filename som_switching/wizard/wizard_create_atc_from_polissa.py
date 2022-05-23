from osv import osv, fields

class WizardCreateAtc(osv.osv_memory):

    _inherit = "wizard.create.atc.from.polissa"

    def onchange_section(self, cursor, uid, ids, section_id):

        seccio_obj = self.pool.get('crm.case.section')
        seccio = seccio_obj.read(cursor, uid, section_id, ['code'])['code']

        if seccio == 'ATCF':
            self.mostrar_tag = True
        else:
            self.mostrar_tag = False

    _columns = {
        'tag': fields.many2one('giscedata.atc.tag', "Etiqueta"),
        'mostrar_tag': fields.boolean(u'Mostrar_tag'),
    }
    _defaults = {
        'mostrar_tag': lambda *a: False,
    }
WizardCreateAtc()