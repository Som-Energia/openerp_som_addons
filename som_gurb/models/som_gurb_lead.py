from osv import osv, fields
from tools.translate import _


class SomGurbLead(osv.osv):
    _name = "som.gurb.lead"
    _rec_name = "cups_id"
    _description = _("Lead de Gurb CUPS en grup de generació urbana")

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

    def get_polissa_gurb_cups(self, cursor, uid, grub_lead_id, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")

        gurb_vals = self.read(cursor, uid, grub_lead_id, ["cups_id", "gurb_id", "owner_cups"])

        search_params = [
            ("state", "=", "activa"),
            ("cups", "=", gurb_vals["cups_id"][0]),
        ]
        pol_ids = pol_o.search(cursor, uid, search_params, context=context, limit=1)

        return pol_ids[0] if pol_ids else False

    def get_titular_gurb_cups(self, cursor, uid, grub_lead_id, context=None):
        if context is None:
            context = {}
        pol_o = self.pool.get("giscedata.polissa")
        pol_id = self.get_polissa_gurb_cups(cursor, uid, grub_lead_id, context=context)
        if not pol_id:
            return False
        partner_id = pol_o.read(cursor, uid, pol_id, ['titular'], context=context)
        if partner_id:
            partner_id = partner_id["titular"][0]
        return partner_id

    def create_initial_invoice(self, cursor, uid, grub_lead_id, context=None):
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

        gurb_cups_br = self.browse(cursor, uid, grub_lead_id, context=context)

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

    def sign_and_create_som_grub_cups(self, cursor, uid, grub_lead_ids, context=None):
        if context is None:
            context = {}
        if not isinstance(grub_lead_ids, list):
            grub_lead_ids = [grub_lead_ids]

        errors = []
        invoice_ids = []

        for grub_lead_id in grub_lead_ids:
            try:
                invoice_id, error = self.create_initial_invoice(
                    cursor, uid, grub_lead_id, context=context
                )
                if error:
                    errors.append(error)
                else:
                    invoice_ids.append(invoice_id)
            except Exception as e:
                errors.append(
                    "[GURB CUPS ID {}]: {}".format(
                        grub_lead_id,
                        e.message,
                    )
                )

        return (invoice_ids, errors)

    _columns = {
        "active": fields.boolean("Actiu"),
        "signed": fields.boolean("Firmat", readonly=True),
        "payed": fields.boolean("Pagat", readonly=True),
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True, ondelete="cascade"),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
        "beta_inicial": fields.float("Beta inicial (kWh)", digits=(16, 6)),
        "owner_cups": fields.function(
            _ff_is_owner,
            type="boolean",
            string="Cups de la persona propietària",
            method=True
        ),
        "general_conditions_id": fields.many2one(
            "som.gurb.general.conditions",
            "Condicions generals",
            required=False,
        ),
    }

    _defaults = {
        "active": lambda *a: True,
    }


SomGurbLead()
