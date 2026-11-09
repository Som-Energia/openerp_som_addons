# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


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
        """Schedule social tariff expiry using the manual tariff change flow."""
        polissa_obj = self.pool.get("giscedata.polissa")
        social_tariff_ids = polissa_obj.mapping_tarifa_social(
            cursor, uid, context=context
        ).values()
        wizard_obj = self.pool.get("wizard.change.tariff.social")
        regular_modcon_ids = []

        modcons = self.read(
            cursor, uid, ids,
            ["llista_preu", "polissa_id", "state", "modcontractual_seg"],
            context=context,
        )
        for modcon in modcons:
            pricelist = modcon.get("llista_preu")
            if not pricelist or pricelist[0] not in social_tariff_ids:
                regular_modcon_ids.append(modcon["id"])
                continue

            # Do not create another pending change when a renewal is retried.
            if modcon["state"] != "actiu" or modcon["modcontractual_seg"]:
                continue

            wizard_id = wizard_obj.create(cursor, uid, {
                "polissa_id": modcon["polissa_id"][0],
                "change_type": "to_regular",
            }, context=context)
            wizard_obj.change_to_regular(
                cursor, uid, [wizard_id], context=context
            )

        return super(GiscedataPolissaModcontractual, self).renovar(
            cursor, uid, regular_modcon_ids, context=context
        )


GiscedataPolissaModcontractual()
