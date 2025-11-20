# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import timedelta, date
from oorq.oorq import AsyncMode
from som_polissa.exceptions import exceptions


class WizardChangeTariff(osv.osv_memory):

    _name = "wizard.change.tariff"

    def _default_polissa_id(self, cursor, uid, context=None):
        """Llegim la pólissa"""
        polissa_id = False
        if context:
            polissa_id = context.get("active_id", False)
        return polissa_id

    def _default_change_type(self, cursor, uid, context=None):
        """Llegim el tipus de canvi"""
        change_type = "from_period_to_index"
        if context:
            change_type = context.get("change_type", "from_period_to_index")
        return change_type

    def get_new_pricelist(self, cursor, uid, polissa, context=None):
        polissa_obj = self.pool.get("giscedata.polissa")

        tarifa_codi = polissa.tarifa_codi
        if context.get("forced_tariff"):
            tarifa_codi = context.get("forced_tariff")

        mode_facturacio = polissa.mode_facturacio
        municipi_id = polissa.cups.id_municipi.id

        new_pricelist_browse = polissa_obj.get_pricelist_from_tariff_and_location(
            cursor, uid, tarifa_codi, mode_facturacio, municipi_id, context=context
        )

        return new_pricelist_browse

    def calculate_new_pricelist(self, cursor, uid, polissa, tarifa_codi, context=None):
        polissa_obj = self.pool.get("giscedata.polissa")
        mode_fact_obj = self.pool.get("giscedata.polissa.mode.facturacio")
        municipi_id = polissa.cups.id_municipi.id

        # Choose price list dict
        mode_fact_obj.search
        mode_facturacio = 'atr'  # TODO: From mode_fact_obj

        new_pricelist_browse = polissa_obj.get_pricelist_from_tariff_and_location(
            cursor, uid, tarifa_codi, mode_facturacio, municipi_id, context=context
        )
        return new_pricelist_browse.id

    def validate_polissa_can_change(
        self, cursor, uid, polissa, only_standard_prices=False, context=None
    ):
        if context is None:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")

        pol_obj.check_modifiable_polissa(cursor, uid, polissa.id, context=context)

        if only_standard_prices:
            price_list_id = polissa.llista_preu.id
            is_standard_price = pol_obj.is_standard_price_list(
                cursor, uid, price_list_id, context=context
            )
            if not is_standard_price:
                raise exceptions.PolissaNotStandardPrice(polissa.name)

    def send_indexada_modcon_created_email(self, cursor, uid, polissa, context=None):
        if context is None:
            context = {}

        ir_model_data = self.pool.get('ir.model.data')
        account_obj = self.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = self.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, "som_indexada", "email_canvi_tarifa_a_indexada"
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        email_account_id = "info@somenergia.coop"
        if template.get("enforce_from_account", False):
            email_from = template.get("enforce_from_account")[0]
        if not email_from:
            email_from = account_obj.search(cursor, uid, [("email_id", "=", email_account_id)])[0]

        try:
            wiz_send_obj = self.pool.get("poweremail.send.wizard")
            ctx = {
                "active_ids": [polissa.id],
                "active_id": polissa.id,
                "template_id": template_id,
                "src_model": "giscedata.polissa",
                "src_rec_ids": [polissa.id],
                "from": email_from,
                "state": "single",
                "priority": "0",
            }

            params = {"state": "single", "priority": "0", "from": ctx["from"]}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            raise exceptions.FailSendEmail(polissa.name, e)

    def change_tariff(self, cursor, uid, ids, context=None):
        """update data_firma_contracte in polissa
        and data_inici in modcontractual"""
        polissa_obj = self.pool.get("giscedata.polissa")

        wizard = self.browse(cursor, uid, ids[0])
        polissa = wizard.polissa_id
        wizard.pricelist_id
        if not context:
            context = {}

        self.validate_polissa_can_change(cursor, uid, polissa)

        new_pricelist_id = context.get("business_pricelist", False)
        if not new_pricelist_id:
            new_pricelist_id = self.calculate_new_pricelist(cursor, uid, polissa)
        coeficient_k = context.get("coeficient_k", False)

        new_modcon_vals = {
            "mode_facturacio": '',  # TODO CHANGE_AUX_VALUES[change_type]["invoicing_type"],
            # TODO CHANGE_AUX_VALUES[change_type]["invoicing_type"],
            "mode_facturacio_generacio": '',
            "llista_preu": new_pricelist_id,
            "coeficient_k": coeficient_k,
            "coeficient_d": False,
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
                    if not coeficient_k:
                        self.send_indexada_modcon_created_email(cursor, uid, polissa)
        except Exception:
            polissa.send_signal("undo_modcontractual")
            raise exceptions.UnexpectedException()

        wizard.write({"state": "end"})
        return polissa.modcontractuals_ids[0].id

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "polissa_id": fields.many2one("giscedata.polissa", "Contracte", required=True),
        "pricelist": fields.many2one("product.pricelist", "Tarifa"),
    }

    _defaults = {
        "polissa_id": _default_polissa_id,
        "change_type": _default_change_type,
        "state": lambda *a: "init",
    }


WizardChangeTariff()
