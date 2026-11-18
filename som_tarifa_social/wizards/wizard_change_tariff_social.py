# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from datetime import date, timedelta

from oorq.oorq import AsyncMode
from osv import fields, osv
from som_polissa.exceptions import exceptions

logger = logging.getLogger("openerp.{}".format(__name__))


class WizardChangeTariffSocial(osv.osv_memory):

    _name = "wizard.change.tariff.social"

    def _default_polissa_id(self, cursor, uid, context=None):
        """Llegim la pòlissa."""
        return context.get("active_id", False) if context else False

    def _default_change_type(self, cursor, uid, context=None):
        """Llegim el tipus de canvi."""
        return context.get("change_type", "to_social") if context else "to_social"

    def change_to_social(self, cursor, uid, ids, context=None):
        """Canvia a tarifa social."""
        return self.change_tariff(cursor, uid, ids, "to_social", context=context)

    def change_to_regular(self, cursor, uid, ids, context=None):
        """Canvia a tarifa normal."""
        return self.change_tariff(cursor, uid, ids, "to_regular", context=context)

    def change_tariff(self, cursor, uid, ids, change_type, context=None):
        """Crea una modificació contractual per canviar la tarifa."""
        polissa_obj = self.pool.get("giscedata.polissa")
        pricelist_obj = self.pool.get("product.pricelist")
        wizard = self.browse(cursor, uid, ids[0], context=context)
        polissa = wizard.polissa_id
        context = context or {}
        new_pricelist_id = polissa_obj.get_new_tariff_change_social_or_regular(
            cursor, uid, polissa.id, change_type, context=context
        )
        new_pricelist = pricelist_obj.browse(
            cursor, uid, new_pricelist_id, context=context
        )
        mode_facturacio = new_pricelist.compatible_invoicing_modes[0].code
        new_modcon_vals = {
            "mode_facturacio": mode_facturacio,
            "mode_facturacio_generacio": mode_facturacio,
            "llista_preu": new_pricelist_id,
        }
        if context.get("te_auvidi", False):
            new_modcon_vals["te_auvidi"] = True

        try:
            polissa.send_signal("modcontractual")
            polissa_obj.write(
                cursor, uid, polissa.id, new_modcon_vals, context=context
            )

            wz_crear_mc_obj = self.pool.get("giscedata.polissa.crear.contracte")
            ctx = {"active_id": polissa.id}
            wiz_id = wz_crear_mc_obj.create(
                cursor, uid, {"duracio": "nou", "accio": "nou"}, context=ctx
            )
            wiz = wz_crear_mc_obj.browse(cursor, uid, [wiz_id])[0]
            data_activacio = date.today() + timedelta(days=1)
            res = wz_crear_mc_obj.onchange_duracio(
                cursor, uid, [wiz.id], str(data_activacio), wiz.duracio, context=ctx
            )
            if res.get("warning", False):
                polissa.send_signal("undo_modcontractual")
                raise osv.except_osv("Error", res["warning"])

            wiz.write({
                "data_inici": str(data_activacio),
                "data_final": str(data_activacio + timedelta(days=364)),
            })
            # The contract workflow derives the next start from the old end.
            # If it has expired, keep it until today so the new one stays pending.
            current_modcon = polissa.modcontractual_activa
            previous_end = str(data_activacio - timedelta(days=1))
            if current_modcon and current_modcon.data_final < previous_end:
                current_modcon.write({"data_final": previous_end})
            with AsyncMode("sync"):
                wiz.action_crear_contracte()
        except Exception:
            logger.exception(
                "Error creating %s tariff modcontractual for polissa id %s",
                change_type, polissa.id,
            )
            polissa.send_signal("undo_modcontractual")
            raise exceptions.UnexpectedException()

        wizard.write({"state": "end"})
        return polissa.modcontractuals_ids[0].id

    def send_social_mail(self, cursor, uid, ids, context=None):
        """Genera el correu amb la plantilla de la tarifa social."""
        context = context or {}
        wizard = self.browse(cursor, uid, ids[0], context=context)
        tmpl_obj = self.pool.get("poweremail.templates")
        imd_obj = self.pool.get("ir.model.data")

        template_name = {
            "to_social": "social_email",
            "to_regular": "anti_social_email",
        }[wizard.change_type]
        template_id = imd_obj.get_object_reference(
            cursor, uid, "som_tarifa_social", template_name
        )[1]
        context = context.copy()
        context["prefetch"] = False
        logger.debug(
            "Generating poweremail template (id: %s) resource: %s, resource_id: %s",
            template_id, "giscedata.polissa", wizard.polissa_id.id,
        )
        wizard.write({"state": "email_send"})
        return tmpl_obj.generate_mail_sync(
            cursor, uid, template_id, wizard.polissa_id.id, context=context
        )

    _columns = {
        "state": fields.selection(
            [("init", "Init"), ("end", "End"), ("email_send", "Email")],
            "State",
        ),
        "polissa_id": fields.many2one(
            "giscedata.polissa", "Contracte", required=True
        ),
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
        "state": lambda *args: "init",
    }


WizardChangeTariffSocial()
