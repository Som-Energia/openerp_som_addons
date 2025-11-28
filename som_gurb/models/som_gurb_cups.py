# -*- encoding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta
from tools.translate import _
import base64
import logging
import netsvc

logger = logging.getLogger("openerp.{}".format(__name__))

_GURB_CUPS_STATES = [
    ("comming_registration", "Alta pendent al GURB"),
    ("comming_modification", "Modificació pendent al GURB"),
    ("comming_cancellation", "Baixa pendent al GURB"),
    ("active", "Activa"),
    ("cancel", "Baixa"),
    ("draft", "Esborrany"),
    ("atr_pending", "ATR Obert"),
]


def parse_datetime(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.strptime(date_string, "%Y-%m-%d")


class SomGurbGeneralConditions(osv.osv):
    _name = "som.gurb.general.conditions"

    _columns = {
        "active": fields.boolean("Activa"),
        "name": fields.char("Nom", size=64, readonly=False),
        "attachment_id": fields.many2one("ir.attachment", "Document", required=True),
        "lang_id": fields.many2one("res.lang", "Idioma", required=True),
    }


SomGurbGeneralConditions()


class SomGurbCups(osv.osv):
    _name = "som.gurb.cups"
    _rec_name = "cups_id"
    _description = _("CUPS en grup de generació urbana")

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        res = super(SomGurbCups, self).write(cursor, uid, ids, vals, context=context)

        if "cups_id" in vals:
            gurb_cups_o = self.pool.get("som.gurb.cups")
            polissa_id = gurb_cups_o.get_polissa_gurb_cups(cursor, uid, ids[0])
            gurb_cups_o.write(cursor, uid, ids, {"polissa_id": polissa_id})

        return res

    def _ff_is_owner(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        gurb_cau_obj = self.pool.get("som.gurb.cau")
        pol_obj = self.pool.get("giscedata.polissa")

        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_cau_id"]):
            gurb_vals = gurb_cau_obj.read(
                cursor, uid, gurb_cups_vals["gurb_cau_id"][0], ["roof_owner_id"]
            )
            cups_id = self.read(cursor, uid, gurb_cups_vals["id"], ["cups_id"])["cups_id"][0]

            if not gurb_vals["roof_owner_id"]:
                res[gurb_cups_vals["id"]] = False
                continue

            search_params = [
                ("state", "not in", ["baixa", "cancelada"]),
                ("cups", "=", cups_id),
                ("titular", "=", gurb_vals["roof_owner_id"][0])
            ]

            pol_id = pol_obj.search(cursor, uid, search_params, context=context, limit=1)
            res[gurb_cups_vals["id"]] = bool(pol_id)

        return res

    def get_new_beta_percentatge(self, cursor, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        res = self._ff_get_future_beta_percentage(cursor, uid, ids, [], [], context=context)
        for gurb_cups_id in ids:
            if res[gurb_cups_id] == 0:
                res[gurb_cups_id] = self._ff_get_beta_percentage(
                    cursor, uid, [gurb_cups_id], [], [], context=context
                )[gurb_cups_id]
        return res

    def _ff_get_future_beta_percentage(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        gurb_obj = self.pool.get("som.gurb.cau")
        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, [
            "gurb_cau_id", "future_beta_kw", "future_extra_beta_kw", "future_gift_beta_kw"
        ]):
            gurb_cau_id = gurb_cups_vals.get("gurb_cau_id", False)
            if gurb_cau_id:
                generation_power = gurb_obj.read(
                    cursor, uid, gurb_cau_id[0], ["generation_power"]
                )["generation_power"]

                if generation_power:
                    beta_kw = gurb_cups_vals.get("future_beta_kw", 0)
                    extra_beta_kw = gurb_cups_vals.get("future_extra_beta_kw", 0)
                    gift_beta_kw = gurb_cups_vals.get("future_gift_beta_kw", 0)
                    res[gurb_cups_vals["id"]] = (
                        extra_beta_kw + beta_kw + gift_beta_kw) * 100 / generation_power
                else:
                    res[gurb_cups_vals["id"]] = 0
        return res

    def _ff_get_beta_percentage(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        gurb_cau_obj = self.pool.get("som.gurb.cau")
        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, [
            "gurb_cau_id", "beta_kw", "extra_beta_kw", "gift_beta_kw"
        ]):
            gurb_cau_id = gurb_cups_vals.get("gurb_cau_id", False)
            if gurb_cau_id:
                generation_power = gurb_cau_obj.read(
                    cursor, uid, gurb_cau_id[0], ["generation_power"]
                )["generation_power"]

                if generation_power:
                    beta_kw = gurb_cups_vals.get("beta_kw", 0)
                    extra_beta_kw = gurb_cups_vals.get("extra_beta_kw", 0)
                    gift_beta_kw = gurb_cups_vals.get("gift_beta_kw", 0)
                    res[gurb_cups_vals["id"]] = (
                        extra_beta_kw + beta_kw + gift_beta_kw) * 100 / generation_power
                else:
                    res[gurb_cups_vals["id"]] = 0
        return res

    def _ff_active_beta(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        gurb_cups_beta_o = self.pool.get("som.gurb.cups.beta")
        res = dict.fromkeys(ids, False)
        for gurb_cups_id in ids:
            search_params = [
                ("active", "=", True),
                ("future_beta", "=", False),
                ("gurb_cups_id", "=", gurb_cups_id)
            ]
            active_beta_id = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)
            read_vals = ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
            active_beta_vals = {
                "beta_kw": 0.0,
                "extra_beta_kw": 0.0,
                "gift_beta_kw": 0.0,
            }
            if active_beta_id:
                active_beta_vals = gurb_cups_beta_o.read(
                    cursor, uid, active_beta_id[0], read_vals, context=context
                )

            res[gurb_cups_id] = active_beta_vals

        return res

    def _ff_future_beta(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        gurb_cups_beta_o = self.pool.get("som.gurb.cups.beta")
        res = dict.fromkeys(ids, False)
        for gurb_cups_id in ids:
            search_params = [
                ("active", "=", True),
                ("future_beta", "=", True),
                ("gurb_cups_id", "=", gurb_cups_id)
            ]
            future_beta_id = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)
            read_vals = ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
            future_beta_vals = {
                "future_beta_kw": 0.0,
                "future_extra_beta_kw": 0.0,
                "future_gift_beta_kw": 0.0,
            }

            if future_beta_id:
                future_beta_id = gurb_cups_beta_o.read(
                    cursor, uid, future_beta_id[0], read_vals, context=context
                )
                future_beta_vals["future_beta_kw"] = future_beta_id["beta_kw"]
                future_beta_vals["future_extra_beta_kw"] = future_beta_id["extra_beta_kw"]
                future_beta_vals["future_gift_beta_kw"] = future_beta_id["gift_beta_kw"]

            res[gurb_cups_id] = future_beta_vals

        return res

    def get_polissa_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}
        pol_id = self.read(cursor, uid, gurb_cups_id, ["polissa_id"])["polissa_id"][0]
        return pol_id

    def get_titular_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}
        partner_id = self.read(cursor, uid, gurb_cups_id, ["partner_id"])["partner_id"][0]
        return partner_id

    def pay_invoice_gurb(self, cursor, uid, inv_id, context=None):
        if context is None:
            context = {}
        account_o = self.pool.get("account.account")
        invoice_o = self.pool.get("account.invoice")

        # Open before paying
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cursor)
        inv = invoice_o.browse(cursor, uid, inv_id)

        # Paguem factura
        pay_account_id = account_o.search(
            cursor, uid, [('code', '=', '5572000000007')], context=context
        )[0]
        invoice_o.pay_and_reconcile(
            cursor, uid, [inv_id], inv.saldo, pay_account_id, inv.period_id.id, inv.journal_id.id,
            None, None, None, context=context
        )

    def generate_gurb_invoice_base64(self, cursor, uid, inv_id, context=None):
        if context is None:
            context = {}
        service = netsvc.LocalService("report.account.invoice")
        (result, doc_format) = service.create(
            cursor, uid, [inv_id], {}, context
        )
        return base64.b64encode(result)

    def form_activate_gurb_cups_lead(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        if isinstance(gurb_cups_id, list):
            gurb_cups_id = gurb_cups_id[0]

        attach_obj = self.pool.get('ir.attachment')
        invoice_o = self.pool.get("account.invoice")

        # Creem factura
        context["tpv"] = True
        inv_id, err = self.create_initial_invoice(cursor, uid, gurb_cups_id, context=context)
        invoice_o.browse(cursor, uid, inv_id)

        # Paguem factura
        self.pay_invoice_gurb(cursor, uid, inv_id, context=context)

        # Adjuntem la factura al Gurb CUPS
        gurb_cups_br = self.browse(cursor, uid, gurb_cups_id, context=context)
        if inv_id:
            invoice_pdf = self.generate_gurb_invoice_base64(cursor, uid, inv_id, context=context)
            vals = {
                'name': "Fatura inicial GURB CUPS - {}".format(gurb_cups_br.id),
                'datas': invoice_pdf,
                'datas_fname': "factura_inicial_gurb_cups_{}.pdf".format(gurb_cups_br.id),
                'res_model': 'som.gurb.cups',
                'res_id': gurb_cups_id,
            }
            attach_obj.create(cursor, uid, vals, context=context)

        self.generate_gurb_welcome_email(cursor, uid, [gurb_cups_id], context=context)
        self.send_signal(cursor, uid, [gurb_cups_id], "button_create_cups")

    def generate_gurb_welcome_email(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}
        tmpl_obj = self.pool.get("poweremail.templates")
        imd_o = self.pool.get("ir.model.data")

        tmpl = imd_o.get_object_reference(cursor, uid, "som_gurb", "email_gurb_welcome")[1]
        ctx = context.copy()
        ctx['prefetch'] = False

        logger.debug(
            "Generating poweremail template (id: {}) resource: {}".format(tmpl, gurb_cups_id)
        )
        return tmpl_obj.generate_mail_sync(cursor, uid, tmpl, gurb_cups_id, context=ctx)

    def send_gurb_activation_email(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        tmpl_obj = self.pool.get("poweremail.templates")
        imd_o = self.pool.get("ir.model.data")

        tmpl = imd_o.get_object_reference(cursor, uid, "som_gurb", "email_gurb_activation")[1]

        ctx = context.copy()
        ctx['prefetch'] = False
        for gurb_cups in self.browse(cursor, uid, ids, context=ctx):
            resource = gurb_cups.id

            logger.debug(
                "Generating poweremail template (id: {}) resource: {}".format(tmpl, resource)
            )
            tmpl_obj.generate_mail(cursor, uid, tmpl, resource, context=ctx)

    def get_gurb_cups_from_sw_id(self, cursor, uid, sw_id, context=None):
        if context is None:
            context = {}

        switching_obj = self.pool.get("giscedata.switching")

        pol_id = switching_obj.read(
            cursor, uid, sw_id, ["cups_polissa_id"], context=context)["cups_polissa_id"][0]

        return self.get_gurb_cups_from_pol_id(cursor, uid, pol_id, context=context)

    def get_gurb_cups_from_pol_id(self, cursor, uid, pol_id, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")

        search_params = [
            ("polissa_id", "=", pol_id)
        ]

        gurb_cups_ids = gurb_cups_obj.search(cursor, uid, search_params, context=context)

        if len(gurb_cups_ids) == 1:
            return gurb_cups_ids[0]

    def activate_or_modify_gurb_cups(self, cursor, uid, gurb_cups_id, data_inici, context=None):
        if context is None:
            context = {}

        som_gurb_beta_o = self.pool.get("som.gurb.cups.beta")

        gurb_cups_date = self.read(cursor, uid, gurb_cups_id, ["start_date"])["start_date"]
        if not gurb_cups_date:
            write_vals = {
                "start_date": data_inici
            }
            self.write(cursor, uid, gurb_cups_id, write_vals, context=context)
            self.add_service_to_contract(
                cursor, uid, gurb_cups_id, data_inici, context=context
            )

        search_params = [
            ("future_beta", "=", True),
            ("gurb_cups_id", "=", gurb_cups_id),
        ]
        future_beta = som_gurb_beta_o.search(cursor, uid, search_params, context=context)

        if future_beta:
            som_gurb_beta_o.activate_future_beta(
                cursor, uid, future_beta[0], data_inici, context=context
            )
        gurb_cups = self.browse(cursor, uid, gurb_cups_id, context=context)
        if gurb_cups.state == "atr_pending":
            gurb_cups.send_signal(["button_confirm_atr"])
        elif gurb_cups.state == "comming_registration":
            gurb_cups.send_signal(["button_activate_cups"])

    def check_only_one_gurb_service(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        gurb_cau_o = self.pool.get("som.gurb.cau")
        service_o = self.pool.get("giscedata.facturacio.services")

        pol_id = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
        products_ids = gurb_cau_o.get_gurb_products_ids(cursor, uid, context=context)

        search_params = [
            ("polissa_id", "=", pol_id),
            ("producte", "in", products_ids)
        ]

        service_ids = service_o.search(cursor, uid, search_params, context=context)

        if service_ids:
            raise osv.except_osv(
                _("Error"),
                _("Ja hi ha un servei GURB CAU actiu associat. No es pot afegir un altre.")
            )

    def add_service_to_contract(self, cursor, uid, gurb_cups_id, data_inici, context=None):
        if context is None:
            context = {}

        gurb_cau_o = self.pool.get("som.gurb.cau")
        wiz_service_o = self.pool.get("wizard.create.service")
        service_o = self.pool.get("giscedata.facturacio.services")
        polissa_o = self.pool.get("giscedata.polissa")
        gurb_group_o = self.pool.get("som.gurb.group")

        read_vals = ["owner_cups", "gurb_cau_id", "cups_id"]

        gurb_cups_vals = self.read(cursor, uid, gurb_cups_id, read_vals, context=context)

        pol_id = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
        if not pol_id:
            error_title = _("No hi ha pòlisses per aquest CUPS"),
            error_info = _(
                "El CUPS id {} no té pòlissa. No es pot afegir.".format(
                    gurb_cups_vals["cups_id"][0]
                )
            )
            raise osv.except_osv(error_title, error_info)

        pol_state = polissa_o.read(cursor, uid, pol_id, ["state"], context=context)["state"]
        if pol_state not in ["activa", "esborrany"]:
            error_title = _("No hi ha pòlisses actives o en esborrany per aquest CUPS"),
            error_info = _(
                "El CUPS id {} no té pòlisses actives o en esborrany. No es pot afegir.".format(
                    gurb_cups_vals["cups_id"][0]
                )
            )
            raise osv.except_osv(error_title, error_info)

        self.check_only_one_gurb_service(
            cursor, uid, gurb_cups_id, context=context
        )

        imd_obj = self.pool.get("ir.model.data")

        gurb_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]
        owner_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "product_owner_gurb"
        )[1]
        enterprise_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "product_enterprise_gurb"
        )[1]

        read_vals = ["tarifa_codi"]
        quota_product_id = False
        pol_vals = polissa_o.read(cursor, uid, pol_id, read_vals, context=context)
        if gurb_cups_vals["owner_cups"]:
            quota_product_id = owner_product_id
        elif pol_vals["tarifa_codi"] == "2.0TD":
            quota_product_id = gurb_product_id
        elif pol_vals["tarifa_codi"] == "3.0TD":
            quota_product_id = enterprise_product_id
        else:
            raise osv.except_osv("Error tarifa accés", "la tarifa d'accés no és 2.0TD ni 3.0TD")

        gurb_vals = gurb_cau_o.read(
            cursor, uid, gurb_cups_vals["gurb_cau_id"][0], ["gurb_group_id"], context=context
        )

        gurb_group_id = gurb_vals["gurb_group_id"][0]

        pricelist_id = gurb_group_o.read(
            cursor, uid, gurb_group_id, ["pricelist_id"], context=context
        )["pricelist_id"][0]

        # Afegim el servei
        creation_vals = {
            "pricelist_id": pricelist_id,
            "product_id": quota_product_id,
            "data_inici": data_inici,
        }

        wiz_id = wiz_service_o.create(cursor, uid, creation_vals, context=context)

        context["active_ids"] = [pol_id]
        wiz_service_o.create_services(cursor, uid, [wiz_id], context=context)

        search_params = [
            ("polissa_id", "=", pol_id),
            ("data_inici", "=", data_inici),
            ("llista_preus", "=", pricelist_id),
            ("producte", "=", quota_product_id),
        ]

        service_id = service_o.search(cursor, uid, search_params, context=context)
        service_o.write(cursor, uid, service_id, {"forcar_nom": "product"}, context=context)

    def unsubscribe_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        # Donar de baixa Servei Contractat
        self.send_signal(cursor, uid, [gurb_cups_id], "button_coming_cancellation")
        self.write(cursor, uid, gurb_cups_id, {
            "ens_ha_avisat": context.get('ens_ha_avisat', False)})

    def get_gurb_products(self, cursor, uid, context=None):
        if context is None:
            context = {}

        imd_o = self.pool.get("ir.model.data")

        base_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]
        owner_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_owner_gurb"
        )[1]
        enterprise_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_enterprise_gurb"
        )[1]

        products_ids = [base_product_id, owner_product_id, enterprise_product_id]

        return products_ids

    def cancel_gurb_cups(self, cursor, uid, gurb_cups_id, end_date, context=None):
        if context is None:
            context = {}

        state = self.read(cursor, uid, gurb_cups_id, ["state"])["state"]

        if state == "active":
            self.send_signal(cursor, uid, [gurb_cups_id], "button_atr_pending")
        else:
            # Desactivate GURB CUPS, Close Beta, Unsubscribe Service
            self.send_signal(cursor, uid, [gurb_cups_id], "button_cancel_cups")
            self.write(cursor, uid, gurb_cups_id, {"active": False, "end_date": end_date})
            self.terminate_service_gurb_cups(
                cursor, uid, gurb_cups_id, end_date, context=context
            )

    def terminate_service_gurb_cups(self, cursor, uid, gurb_cups_id, end_date, context=None):
        if context is None:
            context = {}

        service_o = self.pool.get("giscedata.facturacio.services")
        wiz_terminate_o = self.pool.get("wizard.terminate.service")

        pol_id = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
        products_ids = self.get_gurb_products(cursor, uid, context=context)

        search_params = [
            ("polissa_id", "=", pol_id),
            ("producte", "in", products_ids),
            ("data_fi", "=", False)
        ]

        service_ids = service_o.search(cursor, uid, search_params, context=context)

        wiz_id = wiz_terminate_o.create(cursor, uid, {'data_final': end_date}, context=context)
        context["active_ids"] = service_ids
        wiz_terminate_o.terminate_services(cursor, uid, [wiz_id], context=context)

    def create_initial_invoice(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        imd_o = self.pool.get("ir.model.data")
        invoice_o = self.pool.get("account.invoice")
        account_o = self.pool.get("account.account")
        journal_o = self.pool.get("account.journal")
        payment_type_o = self.pool.get("payment.type")
        invoice_line_o = self.pool.get("account.invoice.line")
        product_o = self.pool.get("product.product")
        pricelist_o = self.pool.get("product.pricelist")

        invoice_account_code = "705000000104"
        journal_code = "FACT_GURB"
        payment_type_code = "TRANSFERENCIA_CSB"

        if context.get("tpv"):
            payment_type_code = "COBRAMENT_TARGETA"

        gurb_cups_br = self.browse(cursor, uid, gurb_cups_id, context=context)

        if gurb_cups_br.initial_invoice_id:
            error = "[GURB CUPS ID {}]: La factura d'inscripció ja existeix.".format(
                gurb_cups_br.id,
            )
            return (False, error)

        partner_id = self.get_titular_gurb_cups(
            cursor, uid, gurb_cups_br.id, context=context
        )

        if not partner_id:
            error = "[GURB CUPS ID {}]: Error al buscar el titular de la pòlissa associada.".format(
                gurb_cups_br.id,
            )
            return (False, error)

        # Initial quota base gurb
        product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "initial_quota_gurb"
        )[1]
        product_br = product_o.browse(cursor, uid, product_id, context=context)

        # Get product price_unit from GURB pricelist
        price_unit = pricelist_o.price_get(
            cursor,
            uid,
            [gurb_cups_br.gurb_cau_id.gurb_group_id.pricelist_id.id],
            product_id,
            gurb_cups_br.beta_kw,
        )[gurb_cups_br.gurb_cau_id.gurb_group_id.pricelist_id.id]

        # Create invoice line
        gurb_line = invoice_line_o.product_id_change(  # Get line default values
            cursor,
            uid,
            [],
            product=product_br.id,
            uom=product_br.uom_id.id,
            partner_id=partner_id,
            type="out_invoice",
        ).get("value", {})
        gurb_line["invoice_line_tax_id"] = [(6, 0, gurb_line.get("invoice_line_tax_id", []))]
        invoice_line_account_ids = account_o.search(
            cursor, uid, [("code", "=", invoice_account_code)], context=context
        )[0]
        gurb_line.update({
            "name": "Cost d'adhesió {}".format(gurb_cups_br.gurb_cau_id.gurb_group_id.name),
            "product_id": product_id,
            "price_unit": price_unit,
            "quantity": 1,
            "account_id": invoice_line_account_ids,
        })
        # Create invoice
        journal_ids = journal_o.search(
            cursor, uid, [("code", "=", journal_code)], context=context
        )
        payment_type_id = payment_type_o.search(
            cursor, uid, [("code", "=", payment_type_code)], context=context
        )[0]

        invoice_lines = [
            (0, 0, gurb_line)
        ]
        invoice_vals = {
            "partner_id": partner_id,
            "type": "out_invoice",
            "invoice_line": invoice_lines,
            "origin": "GURBCUPSID{}".format(gurb_cups_br.id),
            "origin_date_invoice": datetime.today().strftime("%Y-%m-%d"),
            "date_invoice": datetime.today().strftime("%Y-%m-%d")
        }
        invoice_vals.update(invoice_o.onchange_partner_id(  # Get invoice default values
            cursor, uid, [], "out_invoice", partner_id).get("value", {})
        )
        invoice_vals.update({"payment_type": payment_type_id})

        invoice_account_ids = account_o.search(
            cursor, uid, [("code", "=", '430000000000')], context=context
        )
        if invoice_account_ids:
            invoice_vals.update({"account_id": invoice_account_ids[0]})
        if journal_ids:
            invoice_vals.update({"journal_id": journal_ids[0]})

        invoice_id = invoice_o.create(cursor, uid, invoice_vals, context=context)
        invoice_o.button_reset_taxes(cursor, uid, [invoice_id])

        # Update reference
        write_vals = {
            "initial_invoice_id": invoice_id,
        }
        self.write(cursor, uid, gurb_cups_br.id, write_vals, context=context)

        return (invoice_id, False)

    def create_initial_invoices(self, cursor, uid, gurb_cups_ids, context=None):
        if context is None:
            context = {}
        if not isinstance(gurb_cups_ids, list):
            gurb_cups_ids = [gurb_cups_ids]

        errors = []
        invoice_ids = []

        for gurb_cups_id in gurb_cups_ids:
            try:
                invoice_id, error = self.create_initial_invoice(
                    cursor, uid, gurb_cups_id, context=context
                )
                if error:
                    errors.append(error)
                else:
                    invoice_ids.append(invoice_id)
            except Exception as e:
                errors.append(
                    "[GURB CUPS ID {}]: {}".format(
                        gurb_cups_id,
                        e.message,
                    )
                )

        return (invoice_ids, errors)

    def sign_gurb(self, cursor, uid, gurb_cups_id, context=None):
        if not context:
            context = {}

        self.write(cursor, uid, gurb_cups_id, {'signed': True})

    def process_signature_callback(self, cursor, uid, gurb_cups_id, context=None):
        if not context:
            context = {}
        process_data = context.get('process_data', False)
        if process_data:
            method_name = process_data.get('callback_method', False)
            method = getattr(self, method_name)
            if method:
                method(cursor, uid, gurb_cups_id, context=context)

    def onchange_cups_id(self, cursor, uid, ids, cups_id):
        lang_o = self.pool.get("res.lang")
        pol_o = self.pool.get("giscedata.polissa")
        gurb_conditions_o = self.pool.get("som.gurb.general.conditions")

        res = {
            "value": {},
            "domain": {},
            "warning": {},
        }

        search_params = [
            ("state", "in", ["activa", "esborrany"]),
            ("cups", "=", cups_id),
        ]
        pol_ids = pol_o.search(cursor, uid, search_params, limit=1)

        if pol_ids:
            pol_br = pol_o.browse(cursor, uid, pol_ids[0])

            lang = pol_br.titular.lang

            search_params = [
                ("code", "=", lang)
            ]

            lang_id = lang_o.search(cursor, uid, search_params)

            if lang_id:
                search_params = [
                    ("lang_id", "=", lang_id),
                    ("active", "=", True)
                ]
                conditions_id = gurb_conditions_o.search(cursor, uid, search_params)
                if conditions_id:
                    res["value"]["general_conditions_id"] = conditions_id[0]
                    if ids:
                        self.write(cursor, uid, ids, {"general_conditions_id": conditions_id[0]})

        return res

    def change_state(self, cursor, uid, ids, new_state, context=None):
        write_values = {
            "state": new_state,
            "state_date": datetime.now().strftime("%Y-%m-%d")
        }
        for record_id in ids:
            self.write(cursor, uid, ids, write_values, context=context)

    def send_signal(self, cursor, uid, ids, signals):
        """Enviem el signal al workflow del som_gurb_cups.
        """
        wf_service = netsvc.LocalService('workflow')
        if not isinstance(signals, list) and not isinstance(signals, tuple):
            signals = [signals]
        for p_id in ids:
            for signal in signals:
                wf_service.trg_validate(uid, 'som.gurb.cups', p_id, signal, cursor)
        return True

    _columns = {
        "active": fields.boolean("Actiu"),
        "start_date": fields.date("Data activació al GURB"),
        "end_date": fields.date("Data sortida GURB"),
        "inscription_date": fields.date("Data d'inscripció al GURB"),
        "gurb_cau_id": fields.many2one("som.gurb.cau", "GURB", required=True, ondelete="cascade"),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
        "polissa_id": fields.many2one("giscedata.polissa", "Pòlissa", readonly=False),
        "partner_id": fields.related(
            "polissa_id",
            "titular",
            type="many2one",
            relation="res.partner",
            string="Client",
            store=False,
            readonly=True,
        ),
        "polissa_state": fields.related(
            "polissa_id",
            "state",
            type="char",
            relation="giscedata.polissa",
            string="Estat pòlissa",
            store=False,
            readonly=True,
        ),
        "betas_ids": fields.one2many("som.gurb.cups.beta", "gurb_cups_id", "Betes"),
        "beta_kw": fields.function(
            _ff_active_beta,
            string="Beta (kW)",
            type="float",
            digits=(10, 3),
            method=True,
            multi="betas",
        ),
        "extra_beta_kw": fields.function(
            _ff_active_beta,
            string="Extra Beta (kW)",
            type="float",
            digits=(10, 3),
            method=True,
            multi="betas",
        ),
        "gift_beta_kw": fields.function(
            _ff_active_beta,
            string="Beta regal (kW)",
            type="float",
            digits=(10, 3),
            method=True,
            multi="betas",
        ),
        "future_beta_kw": fields.function(
            _ff_future_beta,
            string="Beta futur (kW)",
            type="float",
            digits=(10, 3),
            method=True,
            multi="future_betas",
        ),
        "future_extra_beta_kw": fields.function(
            _ff_future_beta,
            string="Extra Beta futur (kW)",
            type="float",
            digits=(10, 3),
            method=True,
            multi="future_betas",
        ),
        "future_gift_beta_kw": fields.function(
            _ff_future_beta,
            string="Beta regal futur (kW)",
            type="float",
            digits=(10, 3),
            method=True,
            multi="future_betas",
        ),
        "beta_percentage": fields.function(
            _ff_get_beta_percentage,
            type="float",
            string="Total Beta (%)",
            digits=(12, 4),
            method=True,
        ),
        "future_beta_percentage": fields.function(
            _ff_get_future_beta_percentage,
            type="float",
            string="Total Beta (%)",
            digits=(12, 4),
            method=True,
        ),
        "owner_cups": fields.function(
            _ff_is_owner,
            type="boolean",
            string="Persona propietària",
            method=True
        ),
        "initial_invoice_id": fields.many2one("account.invoice", "Factura"),
        "general_conditions_id": fields.many2one(
            "som.gurb.general.conditions",
            "Condicions generals",
            required=False,
        ),
        "invoice_state": fields.related(
            "initial_invoice_id",
            "state",
            type="char",
            relation="account.invoice",
            string="Estat factura",
            store=False,
            readonly=True,
        ),
        "signed": fields.boolean("Signed", readonly=1),
        "quota_product_id": fields.many2one("product.product", "Produce quota mensual"),
        "state": fields.selection(_GURB_CUPS_STATES, "Estat del titular", readonly=True),
        "state_date": fields.date("Data de l'estat"),
        "ens_ha_avisat": fields.boolean(
            "Ens ha avisat",
            help="No és un canvi sobrevingut, sinó que estem informats i ho hem gestionat."),
    }

    _defaults = {
        "active": lambda *a: True,
        "extra_beta_kw": lambda *a: 0,
        "gift_beta_kw": lambda *a: 0,
        "ens_ha_avisat": lambda *a: False,
        "state": lambda *a: "draft",
    }


SomGurbCups()


class SomGurbCupsBeta(osv.osv):
    _name = "som.gurb.cups.beta"
    _description = _("Log of betas and changes for som.gurb.cups")
    _order = "start_date desc"

    def activate_future_beta(self, cursor, uid, future_beta_id, data_inici, context=None):
        if context is None:
            context = {}

        beta_browse = self.browse(cursor, uid, future_beta_id, context=context)

        mod_number = int(beta_browse.name)
        previous_mod_number = mod_number - 1

        if previous_mod_number > 0:
            gurb_cups_id = beta_browse.gurb_cups_id.id
            search_vals = [
                ("gurb_cups_id", "=", gurb_cups_id),
                ("name", "=", previous_mod_number)
            ]
            actual_beta = self.search(cursor, uid, search_vals, context=context, limit=1)

            end_date = (
                parse_datetime(data_inici) - timedelta(days=1)
            ).strftime("%Y-%m-%d")

            write_vals = {
                "end_date": end_date,
                "active": False,
            }
            self.write(cursor, uid, actual_beta, write_vals, context=context)

        write_vals = {
            "start_date": data_inici,
            "future_beta": False,
        }
        self.write(cursor, uid, future_beta_id, write_vals, context=context)

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}

        context['active_test'] = False
        betas_ids = self.search(
            cursor, uid, [('gurb_cups_id', '=', vals['gurb_cups_id'])], context=context
        )
        vals['name'] = len(betas_ids) + 1

        res = super(SomGurbCupsBeta, self).create(
            cursor, uid, vals, context=context
        )

        return res

    _columns = {
        "active": fields.boolean("Activa"),
        "name": fields.char("Codi modificació", size=64, readonly=True),
        "start_date": fields.date("Data inici", required=True),
        "end_date": fields.date("Data fi"),
        "gurb_cups_id": fields.many2one(
            "som.gurb.cups", "GURB CUPS", required=True, ondelete="cascade"
        ),
        "beta_kw": fields.float(
            "Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
        "extra_beta_kw": fields.float(
            "Extra Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
        "gift_beta_kw": fields.float(
            "Beta regal (kW)",
            digits=(10, 3),
            required=True,
        ),
        "future_beta": fields.boolean("Beta de futur"),
    }

    _sql_constraints = [
        ('seq_unique',
         'unique (gurb_cups_id, name)',
         _('The combination of name and gurb_cups_id must be unique for this register!')),
    ]


SomGurbCupsBeta()
