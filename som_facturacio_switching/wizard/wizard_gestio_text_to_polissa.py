# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class WizardGestioTextToPolissa(osv.osv_memory):


    _name = 'wizard.gestio.text.to.polissa'
    _inherit = 'wizard.gestio.text.to.polissa'

    def get_polisses_ids(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get("active_ids")
        polissa_o = self.pool.get('giscedata.polissa')
        from_model = context.get('from_model', 'giscedata.polissa')
        if from_model == "giscedata.facturacio.importacio.linia":
            line_obj = self.pool.get(from_model)
            cups_obj = self.pool.get('giscedata.cups.ps')
            polissa_ids = []
            for _id in active_ids:
                f1 = line_obj.browse(cursor, uid, _id)
                search_params = [
                    ('cups.name', 'ilike', '{}%'.format(f1.cups_text[:20])),
                    ('data_alta','<=', f1.fecha_factura_desde),
                    '|', ('data_baixa','=', False),
                    ('data_baixa','>=', f1.fecha_factura_hasta)
                ]
                pol_id = polissa_o.search(cursor, uid, search_params, context={'active_test': False})
                if len(pol_id) > 1:
                    raise osv.except_osv(_('Error!'), _("Trobades més d'una pòlissa per l'F1 amb cups {}").format(f1.cups_text))
                if not pol_id:
                    raise osv.except_osv(_('Error!'), _("No s'ha trobat pòlissa per l'F1 amb cups {}").format(f1.cups_text))
                polissa_ids.append(pol_id[0])

        elif from_model != "giscedata.polissa":
            polissa_ids = super(WizardGestioTextToPolissa, self).get_polisses_ids(
                cursor, uid, ids, context=context
            )

        else:
            polissa_ids = context.get("active_ids") or [context.get("active_id")]

        return list(set(polissa_ids))

WizardGestioTextToPolissa()