# -*- encoding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from tools.translate import _
import logging

logger = logging.getLogger("openerp.{}".format(__name__))


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

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}

        gurb_cups_id = super(SomGurbCups, self).create(cursor, uid, vals, context=context)

        if "cups_id" in vals:
            gurb_cups_o = self.pool.get("som.gurb.cups")
            polissa_id = gurb_cups_o.get_polissa_gurb_cups(cursor, uid, gurb_cups_id)
            gurb_cups_o.write(cursor, uid, gurb_cups_id, {"polissa_id": polissa_id})

        return gurb_cups_id

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

        gurb_obj = self.pool.get("som.gurb")
        pol_obj = self.pool.get("giscedata.polissa")

        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_id"]):
            gurb_vals = gurb_obj.read(cursor, uid, gurb_cups_vals["gurb_id"][0], ["roof_owner_id"])
            cups_id = self.read(cursor, uid, gurb_cups_vals["id"], ["cups_id"])["cups_id"][0]

            if not gurb_vals["roof_owner_id"]:
                res[gurb_cups_vals["id"]] = False
                continue

            search_params = [
                ("state", "=", "activa"),
                ("cups", "=", cups_id),
                ("titular", "=", gurb_vals["roof_owner_id"][0])
            ]

            pol_id = pol_obj.search(cursor, uid, search_params, context=context, limit=1)
            res[gurb_cups_vals["id"]] = bool(pol_id)

        return res

    def _ff_get_beta_percentage(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        gurb_obj = self.pool.get("som.gurb")
        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_id", "beta_kw", "extra_beta_kw"]):
            gurb_id = gurb_cups_vals.get("gurb_id", False)
            if gurb_id:
                generation_power = gurb_obj.read(
                    cursor, uid, gurb_id[0], ["generation_power"]
                )["generation_power"]

                if generation_power:
                    beta_kw = gurb_cups_vals.get("beta_kw", 0)
                    extra_beta_kw = gurb_cups_vals.get("extra_beta_kw", 0)
                    res[gurb_cups_vals["id"]] = (extra_beta_kw + beta_kw) * 100 / generation_power
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
                ("gurb_cups_id", "=", gurb_cups_id)
            ]
            active_beta_id = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)
            read_vals = ["beta_kw", "extra_beta_kw"]
            active_beta_vals = {
                "beta_kw": 0.0,
                "extra_beta_kw": 0.0
            }
            if active_beta_id:
                active_beta_vals = gurb_cups_beta_o.read(
                    cursor, uid, active_beta_id[0], read_vals, context=context
                )

            res[gurb_cups_id] = active_beta_vals

        return res

    def get_polissa_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")

        gurb_vals = self.read(cursor, uid, gurb_cups_id, ["cups_id", "gurb_id", "owner_cups"])

        search_params = [
            ("state", "in", ["activa", "esborrany"]),
            ("cups", "=", gurb_vals["cups_id"][0]),
        ]
        pol_ids = pol_o.search(cursor, uid, search_params, context=context, limit=1)

        return pol_ids[0] if pol_ids else False

    def get_titular_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}
        pol_o = self.pool.get("giscedata.polissa")
        pol_id = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
        if not pol_id:
            return False
        partner_id = pol_o.read(cursor, uid, pol_id, ['titular'], context=context)
        if partner_id:
            partner_id = partner_id["titular"][0]
        return partner_id

    def add_service_to_contract(self, cursor, uid, ids, data_inici, context=None):
        if context is None:
            context = {}

        gurb_o = self.pool.get("som.gurb")
        wiz_service_o = self.pool.get("wizard.create.service")
        imd_o = self.pool.get("ir.model.data")

        owner_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_owner_gurb"
        )[1]

        gurb_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]

        for gurb_cups_id in ids:
            gurb_vals = self.read(cursor, uid, gurb_cups_id, ["cups_id", "gurb_id", "owner_cups"])

            pol_id = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
            if not pol_id:
                error_title = _("No hi ha pòlisses actives per aquest CUPS"),
                error_info = _(
                    "El CUPS id {} no té pòlisses actives. No es pot afegir cap servei".format(
                        gurb_vals["cups_id"][0]
                    )
                )
                raise osv.except_osv(error_title, error_info)

            # Get related GURB service pricelist
            pricelist_id = gurb_o.read(
                cursor, uid, gurb_vals["gurb_id"][0], ["pricelist_id"], context=context
            )["pricelist_id"]

            # Afegim el servei
            creation_vals = {
                "pricelist_id": pricelist_id,
                "product_id": owner_product_id if gurb_vals["owner_cups"] else gurb_product_id,
                "data_inici": data_inici,
            }

            wiz_id = wiz_service_o.create(cursor, uid, creation_vals, context=context)

            context['active_ids'] = [pol_id]
            wiz_service_o.create_services(cursor, uid, [wiz_id], context=context)

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
            [gurb_cups_br.gurb_id.pricelist_id.id],
            product_id,
            gurb_cups_br.beta_kw,
        )[gurb_cups_br.gurb_id.pricelist_id.id]

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
        gurb_line.update({
            "name": "Quota inicial Gurb",
            "product_id": product_id,
            "price_unit": price_unit,
            "quantity": gurb_cups_br.beta_kw,
        })

        # Create invoice
        invoice_account_ids = account_o.search(
            cursor, uid, [("code", "=", "430000000000")], context=context
        )
        journal_ids = journal_o.search(
            cursor, uid, [("code", "=", "VENTA")], context=context
        )
        payment_type_id = payment_type_o.search(
            cursor, uid, [("code", "=", "TRANSFERENCIA_CSB")], context=context
        )[0]
        invoice_lines = [
            (0, 0, gurb_line)
        ]
        invoice_vals = {
            "partner_id": partner_id,
            "type": "out_invoice",
            "invoice_line": invoice_lines,
            "origin": "GURBCUPSID{}".format(gurb_cups_br.id),
        }
        invoice_vals.update(invoice_o.onchange_partner_id(  # Get invoice default values
            cursor, uid, [], "out_invoice", partner_id).get("value", {})
        )
        invoice_vals.update({"payment_type": payment_type_id})

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

    _columns = {
        "active": fields.boolean("Actiu"),
        "start_date": fields.date("Data entrada GURB", required=True),
        "end_date": fields.date("Data sortida GURB",),
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True, ondelete="cascade"),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
        "polissa_id": fields.many2one("giscedata.polissa", "Pòlissa", readonly=True),
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
        "beta_percentage": fields.function(
            _ff_get_beta_percentage,
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
        "signed": fields.boolean("Signed", readonly=1)
    }

    _defaults = {
        "active": lambda *a: True,
        "extra_beta_kw": lambda *a: 0,
        "start_date": lambda *a: str(datetime.today()),
    }


SomGurbCups()


class SomGurbCupsBeta(osv.osv):
    _name = "som.gurb.cups.beta"
    _description = _("Log of betas and changes for som.gurb.cups")
    _order = "start_date desc"

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
        'name': fields.char('Codi modificació', size=64, readonly=True),
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
    }

    _sql_constraints = [
        ('seq_unique',
         'unique (gurb_cups_id, name)',
         _('The combination of name and gurb_cups_id must be unique for this register!')),
    ]


SomGurbCupsBeta()
