# -*- coding: utf-8 -*-
from osv import osv


class crm_case(osv.osv):
    """Extensió del crm.case per bloquejar el tancament de casos que son consultes de pobresa"""

    _name = "crm.case"
    _inherit = "crm.case"

    def case_close(self, cr, uid, ids, *args):
        imd_obj = self.pool.get('ir.model.data')
        section_id = imd_obj.get_object_reference(
            cr, uid, 'giscedata_facturacio_comer_bono_social',
            'crm_section_bono_social_consulta_pobresa'
        )[1]

        if args and args[0] and args[0].get('origin', False) == 'som.consulta.pobresa':
            consultes = self.browse(cr, uid, ids)
            for consulta in consultes:
                if consulta.section_id.id == section_id:
                    raise osv.except_osv(
                        "No es pot tancar el cas",
                        "Aquest CRM Case s'ha de gestionar des de la vista de Consultes Pobresa")

        return super(crm_case, self).case_close(cr, uid, ids, *args)


crm_case()
