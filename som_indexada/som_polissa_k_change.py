# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

from utils import calculate_new_indexed_prices

import logging

logger = logging.getLogger("openerp.{}".format(__name__))


class SomPolissaKChange(osv.osv):
    _name = "som.polissa.k.change"
    _description = _("Canvi de K de pòlissa")

    def compute_simulation(self, cursor, uid, ids, context=None):
        pol_obj = self.pool.get('giscedata.polissa')
        for record in self.browse(cursor, uid, ids, context):
            if not record.partner_id:
                continue
            partner_id = record.partner_id.id
            import_total_anual_nova_amb_impost = 0
            import_total_anual_antiga_amb_impost = 0
            pol_ids = pol_obj.search(cursor, uid, [
                ('titular', '=', partner_id),
                ('state', '=', 'activa'),
            ])
            for pol in pol_ids:
                context['partner_id'] = partner_id
                pol = pol_obj.browse(cursor, uid, pol, context=context)
                data = calculate_new_indexed_prices(
                    cursor, uid, pol, context=context
                )
                import_total_anual_nova_amb_impost += data['import_total_anual_nova_amb_impost']
                import_total_anual_antiga_amb_impost += data['import_total_anual_antiga_amb_impost']

            write_vals = {
                'import_total_anual_nova_amb_impost': import_total_anual_nova_amb_impost,
                'import_total_anual_antiga_amb_impost': import_total_anual_antiga_amb_impost
            }
            self.write(cursor, uid, [record.id], write_vals, context=context)

    def calculate_multipunt_values(self, cursor, uid, context=None):
        if context is None:
            context = {}

        search_params = [('partner_id', '!=', False)]
        k_change_ids = self.search(cursor, uid, search_params, context=context)

        self.compute_simulation(cursor, uid, k_change_ids, context=context)

    _columns = {
        "polissa_id": fields.many2one("giscedata.polissa", "Pòlissa"),
        "k_old": fields.float("K Antiga"),
        "k_new": fields.float("K Nova"),
        "partner_id": fields.many2one("res.partner", "Partner"),
        "import_total_anual_nova_amb_impost": fields.float("Estimat Nova"),
        "import_total_anual_antiga_amb_impost": fields.float("Estimat Antiga"),
    }

    _sql_constraints = [(
        "polissa_id_id_uniq",
        "unique(polissa_id)",
        "La pòlissa ha de ser única"
    )]


SomPolissaKChange()
