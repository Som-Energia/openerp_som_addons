# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import timedelta, date
from oorq.oorq import AsyncMode
from som_polissa.exceptions import exceptions


TARIFA_CODIS_INDEXADA = {
    "2.0TD": {
        "peninsula": "pricelist_indexada_20td_peninsula",
        "canaries": "pricelist_indexada_20td_canaries",
        "balears": "pricelist_indexada_20td_balears",
    },
    "3.0TD": {
        "peninsula": "pricelist_indexada_30td_peninsula",
        "canaries": "pricelist_indexada_30td_canaries",
        "balears": "pricelist_indexada_30td_balears",
    },
    "6.1TD": {
        "peninsula": "pricelist_indexada_61td_peninsula",
        "canaries": "pricelist_indexada_61td_canaries",
        "balears": "pricelist_indexada_61td_balears",
    },
}

TARIFA_CODIS_PERIODES = {
    "2.0TD": {
        "peninsula": "pricelist_periodes_20td_peninsula",  # id 101
        "canaries": "pricelist_periodes_20td_insular",  # id 120
        "balears": "pricelist_periodes_20td_insular",
    },
    "3.0TD": {
        "peninsula": "pricelist_periodes_30td_peninsula",  # id 102
        "canaries": "pricelist_periodes_30td_insular",  # id 121
        "balears": "pricelist_periodes_30td_insular",
    },
    "6.1TD": {
        "peninsula": "pricelist_periodes_61td_peninsula",  # id 103
        "canaries": "pricelist_periodes_61td_insular",  # id 122
        "balears": "pricelist_periodes_61td_insular",
    },
}

CHANGE_AUX_VALUES = {
    "from_index_to_period": {
        "comments": "periodes",
        "invoicing_type": "atr",
    },
    "from_period_to_index": {
        "comments": "indexada",
        "invoicing_type": "index",
    },
}

FISCAL_POSITIONS_CANARIES = [19, 25, 33, 34, 38, 39]


class WizardChangeToIndexada(osv.osv_memory):

    _name = "wizard.change.to.indexada"

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

    def _get_list_cups_balears(self, cursor, uid, context=None):
        xml_id_prov_balears = "ES07"
        IrModel = self.pool.get("ir.model.data")
        id_prov_balears = IrModel._get_obj(
            cursor,
            uid,
            "l10n_ES_toponyms",
            xml_id_prov_balears,
        ).id

        sql_array = """
            select array_agg(gcp.id) as cup_ids
            from giscedata_cups_ps gcp
            inner join res_municipi rm on rm.id = gcp.id_municipi
            inner join res_country_state rcs on rcs.id = rm.state
            where rcs.id = %s and gcp.active=True
        """
        cursor.execute(sql_array, (id_prov_balears,))
        res = cursor.dictfetchone()["cup_ids"]
        return res or []

    def _get_location_polissa(self, cursor, uid, polissa):
        if (
            polissa.fiscal_position_id
            and polissa.fiscal_position_id.id in FISCAL_POSITIONS_CANARIES
        ):
            return "canaries"
        elif polissa.cups.id in self._get_list_cups_balears(cursor, uid):
            return "balears"
        else:
            return "peninsula"

    def get_new_pricelist(self, cursor, uid, polissa, context=None):
        IrModel = self.pool.get("ir.model.data")
        Pricelist = self.pool.get("product.pricelist")

        tarifa_codi = polissa.tarifa_codi
        if context.get("forced_tariff"):
            tarifa_codi = context.get("forced_tariff")

        # Choose price list dict
        dict_pricelist_codis = TARIFA_CODIS_PERIODES
        if polissa.mode_facturacio == "index":
            dict_pricelist_codis = TARIFA_CODIS_INDEXADA

        if tarifa_codi not in dict_pricelist_codis:
            raise exceptions.TariffCodeNotSupported(tarifa_codi)

        location = self._get_location_polissa(cursor, uid, polissa)

        search_params = [
            ("module", "=", "som_indexada"),
            ("name", "=", dict_pricelist_codis[tarifa_codi][location]),
        ]

        ir_model_id = IrModel.search(cursor, uid, search_params, context=context)[0]

        new_pricelist_id = IrModel.read(cursor, uid, ir_model_id, ["res_id"], context=context)[
            "res_id"
        ]

        new_pricelist_browse = Pricelist.browse(cursor, uid, new_pricelist_id, context=context)

        return new_pricelist_browse

    def calculate_new_pricelist(self, cursor, uid, polissa, change_type, context=None):
        IrModel = self.pool.get("ir.model.data")
        tarifa_codi = polissa.tarifa_codi

        # Choose price list dict
        dict_tarifa_codis = TARIFA_CODIS_PERIODES
        if change_type == "from_period_to_index":
            dict_tarifa_codis = TARIFA_CODIS_INDEXADA

        if tarifa_codi not in dict_tarifa_codis:
            raise exceptions.TariffCodeNotSupported(tarifa_codi)

        location = self._get_location_polissa(cursor, uid, polissa)

        new_pricelist_id = IrModel._get_obj(
            cursor,
            uid,
            "som_indexada",
            dict_tarifa_codis[tarifa_codi][location],
        ).id

        return new_pricelist_id

    def _is_standard_price_list(self, cursor, uid, price_list_id, context=None):
        IrModel = self.pool.get("ir.model.data")

        for price_list_mode in (
            TARIFA_CODIS_PERIODES,
            TARIFA_CODIS_INDEXADA,
        ):
            for tarifa_codi, locations in price_list_mode.items():
                for location, semantic_id in locations.items():
                    # TODO: Could this resolution be calculated once?
                    standard_price_list_id = IrModel._get_obj(
                        cursor,
                        uid,
                        "som_indexada",
                        semantic_id,
                    )
                    if price_list_id == standard_price_list_id.id:
                        return True
        return False

    def validate_polissa_can_change(
        self, cursor, uid, polissa, change_type, only_standard_prices=False, context=None
    ):
        if context is None:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")

        pol_obj.check_modifiable_polissa(cursor, uid, polissa.id, context=context)

        if change_type == "from_period_to_index" and polissa.mode_facturacio == "index":
            raise exceptions.PolissaAlreadyIndexed(polissa.name)
        if change_type == "from_index_to_period" and polissa.mode_facturacio == "atr":
            raise exceptions.PolissaAlreadyPeriod(polissa.name)

        if only_standard_prices:
            price_list_id = polissa.llista_preu.id
            is_standard_price = self._is_standard_price_list(cursor, uid, price_list_id, context)
            if not is_standard_price:
                raise exceptions.PolissaNotStandardPrice(polissa.name)

    def send_indexada_modcon_created_email(self, cursor, uid, polissa):
        ir_model_data = self.pool.get("ir.model.data")
        account_obj = self.pool.get("poweremail.core_accounts")
        power_email_tmpl_obj = self.pool.get("poweremail.templates")

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

        except Exception:
            raise exceptions.FailSendEmail(polissa.name)

    def change_to_indexada(self, cursor, uid, ids, context=None):
        """update data_firma_contracte in polissa
        and data_inici in modcontractual"""
        polissa_obj = self.pool.get("giscedata.polissa")

        wizard = self.browse(cursor, uid, ids[0])
        polissa = wizard.polissa_id
        change_type = wizard.change_type
        if not context:
            context = {}

        self.validate_polissa_can_change(cursor, uid, polissa, change_type)

        new_pricelist_id = context.get("business_pricelist", False)
        if not new_pricelist_id:
            new_pricelist_id = self.calculate_new_pricelist(cursor, uid, polissa, change_type)
        coeficient_k = context.get("coeficient_k", False)

        new_modcon_vals = {
            "mode_facturacio": CHANGE_AUX_VALUES[change_type]["invoicing_type"],
            "mode_facturacio_generacio": CHANGE_AUX_VALUES[change_type]["invoicing_type"],
            "llista_preu": new_pricelist_id,
            "coeficient_k": coeficient_k,
            "coeficient_d": False,
        }
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

        wizard.write({"state": "end"})
        return polissa.modcontractuals_ids[0].id

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "change_type": fields.selection(
            [
                ("from_index_to_period", "From index to period"),
                ("from_period_to_index", "From period to index"),
            ],
            "Change type",
            required=True,
        ),
        "polissa_id": fields.many2one("giscedata.polissa", "Contracte", required=True),
    }

    _defaults = {
        "polissa_id": _default_polissa_id,
        "change_type": _default_change_type,
        "state": lambda *a: "init",
    }


WizardChangeToIndexada()
