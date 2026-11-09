# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, timedelta
import logging

from oorq.oorq import AsyncMode
from osv import osv
from som_polissa.exceptions import exceptions


logger = logging.getLogger("openerp.{}.modcontractual".format(__name__))


class GiscedataPolissaModcontractual(osv.osv):

    _inherit = "giscedata.polissa.modcontractual"

    def aplicar_modificacio(self, cursor, uid, mod_id, polissa_id=None):
        result = super(GiscedataPolissaModcontractual, self).aplicar_modificacio(
            cursor, uid, mod_id, polissa_id=polissa_id
        )
        modcon = self.browse(cursor, uid, mod_id)
        polissa_id = polissa_id or modcon.polissa_id.id
        polissa_obj = self.pool.get("giscedata.polissa")
        category_id = self.pool.get("ir.model.data").get_object_reference(
            cursor, uid, "som_tarifa_social", "categ_tarifa_social"
        )[1]
        social_ids = polissa_obj.mapping_tarifa_social(cursor, uid).values()
        add_category = 4
        remove_category = 3
        if modcon.llista_preu.id in social_ids:
            category_command = (add_category, category_id)
        else:
            category_command = (remove_category, category_id)
        polissa_obj.write(cursor, uid, [polissa_id], {
            "category_id": [category_command],
        })
        return result

    def renovar(self, cursor, uid, ids, context=None):
        polissa_obj = self.pool.get("giscedata.polissa")
        social_tariff_ids = polissa_obj.mapping_tarifa_social(
            cursor, uid, context=context
        ).values()
        social_tariff_modcon_ids = []

        modcons = self.read(
            cursor, uid, ids, ["llista_preu", "polissa_id"], context=context
        )
        for modcon in modcons:
            pricelist = modcon.get("llista_preu")
            if not pricelist or pricelist[0] not in social_tariff_ids:
                continue

            polissa_id = modcon["polissa_id"][0]
            polissa = polissa_obj.browse(
                cursor, uid, polissa_id, context=context
            )
            new_pricelist_id = polissa_obj.mapping_tarifa_no_social(
                cursor, uid, polissa_id, context=context
            )
            if not new_pricelist_id:
                raise exceptions.PolissaCannotChangeSocialTariff(
                    polissa.name, "to_regular",
                )
            try:
                polissa.send_signal("modcontractual")
                polissa_obj.write(
                    cursor, uid, polissa.id,
                    {"llista_preu": new_pricelist_id}, context=context,
                )

                wizard_obj = self.pool.get("giscedata.polissa.crear.contracte")
                wizard_context = {"active_id": polissa.id}
                wizard_id = wizard_obj.create(
                    cursor, uid, {"duracio": "nou", "accio": "nou"},
                    context=wizard_context,
                )
                wizard = wizard_obj.browse(
                    cursor, uid, [wizard_id], context=wizard_context
                )[0]
                activation_date = date.today() + timedelta(days=1)
                result = wizard_obj.onchange_duracio(
                    cursor, uid, [wizard.id], str(activation_date),
                    wizard.duracio, context=wizard_context,
                )
                if result.get("warning", False):
                    polissa.send_signal("undo_modcontractual")
                    raise osv.except_osv("Error", result["warning"])

                wizard.write({
                    "data_inici": str(activation_date),
                    "data_final": str(activation_date + timedelta(days=364)),
                })
                with AsyncMode("sync"):
                    wizard.action_crear_contracte()

                social_tariff_modcon_ids.append(modcon["id"])
            except Exception as error:
                polissa.send_signal("undo_modcontractual")
                logger.exception(
                    "Error creating non-social tariff modcontractual for "
                    "polissa id %s: %s", polissa_id, error,
                )
                raise exceptions.UnexpectedException()

        if social_tariff_ids:
            ids = [
                modcon_id for modcon_id in ids
                if modcon_id not in social_tariff_modcon_ids
            ]

        return super(GiscedataPolissaModcontractual, self).renovar(
            cursor, uid, ids, context=context
        )


GiscedataPolissaModcontractual()
