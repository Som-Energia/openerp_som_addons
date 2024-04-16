# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging

logger = logging.getLogger("openerp.{}".format(__name__))


class SomGurbCups(osv.osv):
    _name = "som.gurb.cups"
    _rec_name = "cups_id"
    _description = _("CUPS en grup de generació urbana")

    def _ff_is_owner(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        gurb_obj = self.pool.get("som.gurb")
        pol_obj = self.pool.get("giscedata.polissa")

        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_id"]):
            gurb_vals = gurb_obj.read(cursor, uid, gurb_cups_vals["gurb_id"][0], ["roof_owner_id"])
            cups_id = self.read(cursor, uid, gurb_cups_vals["id"], ["cups_id"])["cups_id"][0]
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
            ("state", "=", "activa"),
            ("cups", "=", gurb_vals["cups_id"][0]),
        ]

        pol_id = pol_o.search(
            cursor, uid, search_params, context=context, limit=1
        )[0]  # TODO: comprovar no empty

        return pol_id

    def get_titular_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}
        pol_o = self.pool.get("giscedata.polissa")
        pol_id = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
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

            pol_ids = self.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)
            if not pol_ids:
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

            context['active_ids'] = pol_ids
            wiz_service_o.create_services(cursor, uid, [wiz_id], context=context)

    def create_initial_invoices(self, cursor, uid, gurb_cups_ids, context=None):
        if context is None:
            context = {}
        if not isinstance(gurb_cups_ids, list):
            gurb_cups_ids = [gurb_cups_ids]

        imd_o = self.pool.get("ir.model.data")
        invoice_o = self.pool.get("account.invoice")
        invoice_line_o = self.pool.get("account.invoice.line")
        product_o = self.pool.get("product.product")
        pricelist_o = self.pool.get("product.pricelist")

        # Initial quota base gurb
        product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "initial_quota_gurb"
        )[1]

        errors = []

        for gurb_cups_br in self.browse(cursor, uid, gurb_cups_ids, context=context):
            # TODO: Més validacions?
            if gurb_cups_br.invoice_ref:
                errors.append(
                    "Initial Invoice {} already exists".format(gurb_cups_br.invoice_ref)
                )
                continue

            partner_id = self.get_titular_gurb_cups(cursor, uid, gurb_cups_br.id, context=context)
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
            gurb_line.update({
                "name": "Quota inicial Gurb",
                "product_id": product_id,
                "price_unit": price_unit,
                "quantity": gurb_cups_br.beta_kw,
            })

            # Create invoice
            invoice_lines = [
                (0, 0, gurb_line)
            ]
            invoice_vals = {
                "partner_id": partner_id,
                "type": "out_invoice",
                "invoice_line": invoice_lines,
            }
            invoice_vals.update(invoice_o.onchange_partner_id(  # Get invoice default values
                cursor, uid, [], "out_invoice", partner_id).get("value", {})
            )
            invoice_id = invoice_o.create(cursor, uid, invoice_vals, context=context)

            # Update reference
            write_vals = {
                "invoice_ref": "account.invoice,{}".format(invoice_id)
            }
            self.write(cursor, uid, gurb_cups_br.id, write_vals, context=context)

        return errors

    _columns = {
        "active": fields.boolean("Actiu"),
        "start_date": fields.date("Data entrada GURB", required=True),
        "end_date": fields.date("Data sortida GURB",),
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True, ondelete="cascade"),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
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
            string="Cups de la persona propietària",
            method=True
        ),
        "invoice_ref": fields.reference(
            "Factura d'inscripció", selection=[("account.invoice", "Factura")], size=128
        ),
    }

    _defaults = {
        "active": lambda *a: True,
        "extra_beta_kw": lambda *a: 0,
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
