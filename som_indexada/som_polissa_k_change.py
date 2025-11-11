# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

from . import utils

import logging

logger = logging.getLogger("openerp.{}".format(__name__))


class SomPolissaKChange(osv.osv):
    _name = "som.polissa.k.change"
    _description = _("Canvi de K de pòlissa")

    def calculate_multipunt_values(self, cursor, uid, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')

        search_params = [('partner_id', '!=', False)]

        k_change_ids = self.search(cursor, uid, search_params, context=context)

        for k_change in k_change_ids:
            partner_id = self.read(
                cursor, uid, k_change, ['partner_id'], context=context
            )['partner_id'][0]

            import_total_anual_nova_amb_impost = 0
            import_total_anual_antiga_amb_impost = 0
            pol_ids = pol_obj.search(cursor, uid, [
                ('titular', '=', partner_id),
                ('state', '=', 'activa'),
            ])
            for pol in pol_ids:
                context['partner_id'] = partner_id
                pol_browse = pol_obj.browse(cursor, uid, pol, context=context)
                data = utils.calculate_new_eie_indexed_prices(
                    cursor, uid, pol_browse, context=context
                )

                import_total_anual_nova_amb_impost += data['import_total_anual_nova_amb_impost']
                import_total_anual_antiga_amb_impost += data['import_total_anual_antiga_amb_impost']

            write_vals = {
                'import_total_anual_nova_amb_impost': import_total_anual_nova_amb_impost,
                'import_total_anual_antiga_amb_impost': import_total_anual_antiga_amb_impost
            }
            self.write(cursor, uid, [k_change], write_vals, context=context)

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
