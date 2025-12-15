# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import timedelta, date
from oorq.oorq import AsyncMode
from som_polissa.exceptions import exceptions


class WizardChangeTariffSocial(osv.osv_memory):

    _name = "wizard.change.tariff.social"

    def _default_polissa_id(self, cursor, uid, context=None):
        """Llegim la pólissa"""
        polissa_id = False
        if context:
            polissa_id = context.get("active_id", False)
        return polissa_id

    def _default_change_type(self, cursor, uid, context=None):
        """Llegim el tipus de canvi"""
        change_type = "to_social"
        if context:
            change_type = context.get("change_type", "to_social")
        return change_type

    def change_to_social(self, cursor, uid, ids, context=None):
        """canvi a tarifa social"""
        return self.change_tariff(
            cursor, uid, ids, "to_social", context=context
        )

    def change_to_regular(self, cursor, uid, ids, context=None):
        """canvi a tarifa normal"""
        return self.change_tariff(
            cursor, uid, ids, "to_regular", context=context
        )

    def change_tariff(self, cursor, uid, ids, change_type, context):
        """canvi a tarifa social"""
        polissa_obj = self.pool.get("giscedata.polissa")
        pricelist_obj = self.pool.get("product.pricelist")
        wizard = self.browse(cursor, uid, ids[0])
        polissa = wizard.polissa_id
        if not context:
            context = {}
        new_pricelist_id = polissa_obj.get_new_tariff_change_social_or_regular(
            cursor, uid, polissa.id, change_type, context=context
        )
        new_pricelist = pricelist_obj.browse(cursor, uid, new_pricelist_id, context=context)
        mode_facturacio = new_pricelist.compatible_invoicing_modes[0].name.lower()
        new_modcon_vals = {
            "mode_facturacio": mode_facturacio,
            "mode_facturacio_generacio": mode_facturacio,
            "llista_preu": new_pricelist_id,
        }
        if context.get("te_auvidi", False):
            new_modcon_vals['te_auvidi'] = True

        try:
            polissa.send_signal("modcontractual")
            polissa_obj.write(cursor, uid, polissa.id, new_modcon_vals, context=context)

            wz_crear_mc_obj = self.pool.get("giscedata.polissa.crear.contracte")
            ctx = {"active_id": polissa.id}
            params = {
                "duracio": "nou",
                "accio": "nou",
            }
            wiz_id = wz_crear_mc_obj.create(cursor, uid, params, context=ctx)
            wiz = wz_crear_mc_obj.browse(cursor, uid, [wiz_id])[0]
            data_activacio = date.today() + timedelta(days=1)
            res = wz_crear_mc_obj.onchange_duracio(
                cursor, uid, [wiz.id], str(data_activacio), wiz.duracio, context=ctx
            )
            if res.get("warning", False):
                polissa.send_signal("undo_modcontractual")
                raise osv.except_osv("Error", res["warning"])
            else:
                wiz.write(
                    {
                        "data_inici": str(data_activacio),
                        "data_final": str(data_activacio + timedelta(days=364)),
                    }
                )

                with AsyncMode("sync"):
                    wiz.action_crear_contracte()
        except Exception:
            polissa.send_signal("undo_modcontractual")
            raise exceptions.UnexpectedException()

        wizard.write({"state": "end"})
        return polissa.modcontractuals_ids[0].id

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "polissa_id": fields.many2one("giscedata.polissa", "Contracte", required=True),
        "pricelist_id": fields.many2one("product.pricelist", "Tarifa"),
        "change_type": fields.selection(
            [("to_social", "To social tariff"), ("to_regular", "To regular tariff")],
            "Change type",
            required=True,
        ),
    }

    _defaults = {
        "polissa_id": _default_polissa_id,
        "change_type": _default_change_type,
        "state": lambda *a: "init",
    }


WizardChangeTariffSocial()
