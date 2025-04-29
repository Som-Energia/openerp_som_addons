# -*- coding: utf-8 -*-
from datetime import datetime
from osv import fields, osv
import netsvc


_tipus_tarifes_lead = [
    ("tarifa_existent", "Tarifa existent (ATR o Fixa)"),
    ("tarifa_provisional", "Tarifa ATR provisional"),
]

_member_quota_payment_types = [
    ("remesa", "Remesa"),
    ("tpv", "Passarel·la de pagament")
]

WWW_DATA_FORM_HEADER = "**** DADES DEL FORMULARI ****"
_MEMBER_FEE_PURPOSE = 'QUOTA SOCI'


class GiscedataCrmLead(osv.OsvInherits):

    _inherit = "giscedata.crm.lead"

    def contract_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        context["lead"] = True

        lead = self.browse(cursor, uid, ids[0])
        context["lang"] = lead.lang

        preus_provisional_energia = {
            "P1": lead.preu_fix_energia_p1,
            "P2": lead.preu_fix_energia_p2,
            "P3": lead.preu_fix_energia_p3,
            "P4": lead.preu_fix_energia_p4,
            "P5": lead.preu_fix_energia_p5,
            "P6": lead.preu_fix_energia_p6,
        }
        if lead.tipus_tarifa_lead == 'tarifa_provisional':
            context["tarifa_provisional"] = {"preus_provisional_energia": preus_provisional_energia}
            if lead.set_custom_potencia:
                preus_provisional_potencia = {
                    "P1": lead.preu_fix_potencia_p1,
                    "P2": lead.preu_fix_potencia_p2,
                    "P3": lead.preu_fix_potencia_p3,
                    "P4": lead.preu_fix_potencia_p4,
                    "P5": lead.preu_fix_potencia_p5,
                    "P6": lead.preu_fix_potencia_p6,
                }
                context["tarifa_provisional"]["preus_provisional_potencia"] = \
                    preus_provisional_potencia

        return super(GiscedataCrmLead, self).contract_pdf(cursor, uid, ids, context=context)

    def _check_and_get_mandatory_fields(
        self, cursor, uid, crml_id, mandatory_fields=[], other_fields=[], context=None
    ):
        if not (context is None or context.get("som_from_activation_lead")):
            if "llista_preu" in mandatory_fields:
                data = self.read(cursor, uid, crml_id, ["tipus_tarifa_lead", "set_custom_potencia"])
                if (
                    data["tipus_tarifa_lead"] == "tarifa_provisional"
                    and data["set_custom_potencia"]
                ):
                    mandatory_fields.pop(mandatory_fields.index("llista_preu"))

        return super(GiscedataCrmLead, self)._check_and_get_mandatory_fields(
            cursor, uid, crml_id, mandatory_fields, other_fields, context
        )

    def onchange_tipus_tarifa_lead(self, cursor, uid, ids, tipus_tarifa_lead):
        res = {
            "value": {"set_custom_potencia": False},
            "domain": {},
            "warning": {},
        }
        if tipus_tarifa_lead == "tarifa_provisional":
            res["value"]["llista_preu"] = False
        return res

    def create_entity_polissa(self, cursor, uid, crml_id, context=None):
        res = super(GiscedataCrmLead, self).create_entity_polissa(
            cursor, uid, crml_id, context=context
        )
        values = {}
        partner_o = self.pool.get("res.partner")

        # recuperem la polissa recent creada del lead
        lead = self.browse(cursor, uid, crml_id, context=context)

        polissa_id = lead.polissa_id.id
        member_number = lead.member_number

        values["soci"] = partner_o.search(cursor, uid, [("ref", "=", member_number)], limit=1)[0]
        values["donatiu"] = lead.donation

        for line in lead.history_line:
            if line.description and line.description.startswith(WWW_DATA_FORM_HEADER):
                values["observacions"] = line.description
                break

        polissa_o = self.pool.get("giscedata.polissa")
        polissa = polissa_o.browse(cursor, uid, polissa_id, context=context)
        if polissa.mode_facturacio != 'atr':
            values['mode_facturacio_generacio'] = polissa.mode_facturacio

        fp_id = polissa_o.calculate_fiscal_position_from_cups(
            cursor, uid,
            polissa.cups.id,
            polissa.cnae.name,
            [potencia.potencia for potencia in polissa.potencies_periode],
            context=context
        )
        if fp_id:
            values['fiscal_position_id'] = fp_id

        if values:
            polissa_o.write(cursor, uid, polissa_id, values, context=context)
        return res

    def onchange_set_custom_potencia(self, cursor, uid, ids, set_custom_potencia):
        res = {
            "value": {},
            "domain": {},
            "warning": {},
        }
        if set_custom_potencia == True:   # noqa: E712
            res["value"]["llista_preu"] = False
        else:
            res["value"]["preu_fix_potencia_p1"] = 0
            res["value"]["preu_fix_potencia_p2"] = 0
            res["value"]["preu_fix_potencia_p3"] = 0
            res["value"]["preu_fix_potencia_p4"] = 0
            res["value"]["preu_fix_potencia_p5"] = 0
            res["value"]["preu_fix_potencia_p6"] = 0

        return res

    def create_entity_titular(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}

        lead = self.browse(cursor, uid, crml_id, context=context)

        if lead.create_new_member:
            context["create_member"] = True

        representative_id = self._create_or_get_representative(
            cursor, uid, lead.persona_firmant_vat, lead.persona_nom, context=context
        )
        if representative_id:
            context["partner_representantive_id"] = representative_id

        res = super(GiscedataCrmLead, self).create_entity_titular(
            cursor, uid, crml_id, context=context
        )

        if lead.member_quota_payment_type == 'remesa':
            self.create_entity_member_bank_payment(cursor, uid, crml_id, context=context)

        return res

    def _create_or_get_representative(self, cursor, uid, vat, name, context=None):
        if context is None:
            context = {}

        partner_o = self.pool.get("res.partner")

        representative_id = None
        if vat:
            if len(vat) <= 9:
                vat = "ES" + vat
            vat = vat.upper()

            representative_ids = partner_o.search(cursor, uid, [("vat", "=", vat)])
            if representative_ids:
                representative_id = representative_ids[0]
            else:
                representative_id = partner_o.create(
                    cursor, uid, {
                        "vat": vat,
                        "name": name,
                    },
                    context=context
                )
        return representative_id

    def create_entity_member_bank_payment(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}

        invoice_o = self.pool.get("account.invoice")
        account_o = self.pool.get("account.account")
        journal_o = self.pool.get("account.journal")
        payment_type_o = self.pool.get("payment.type")
        payment_mode_o = self.pool.get("payment.mode")
        payment_order_o = self.pool.get("payment.order")
        currency_o = self.pool.get("res.currency")
        conf_o = self.pool.get("res.config")
        ir_model_o = self.pool.get("ir.model.data")

        lead = self.browse(cursor, uid, crml_id, context=context)

        if lead.initial_invoice_id:
            raise osv.except_osv('Error', 'Ja existeix una factura de remesa inicial')

        partner_id = lead.partner_id.id
        mandate_id = self.get_or_create_payment_mandate(
            cursor, uid, partner_id, lead.iban, _MEMBER_FEE_PURPOSE, context=context)

        socia_fee_amount = conf_o.get(cursor, uid, "socia_member_fee_amount", "100")
        euro_id = currency_o.search(cursor, uid, [('code', '=', 'EUR')])[0]
        invoice_account_ids = account_o.search(
            cursor, uid, [("code", "=", "100000000000")], context=context
        )

        # Create invoice line
        inv_line = {
            "name": _MEMBER_FEE_PURPOSE,
            "account_id": invoice_account_ids[0],
            "price_unit": socia_fee_amount,
            "quantity": 1,
            "uom_id": 1,
            "company_currency_id": euro_id,
        }

        # Create invoice
        journal_ids = journal_o.search(
            cursor, uid, [("code", "=", "SOCIS")], context=context
        )
        payment_type_id = payment_type_o.search(
            cursor, uid, [("code", "=", "TRANSFERENCIA_CSB")], context=context
        )[0]
        invoice_vals = {
            "number": "QUOTA-SOCIA-LEAD-{}".format(lead.id),
            "partner_id": partner_id,
            "type": "out_invoice",
            "invoice_line": [(0, 0, inv_line)],
            "origin_date_invoice": datetime.today().strftime("%Y-%m-%d"),
            "date_invoice": datetime.today().strftime("%Y-%m-%d"),
            "mandate_id": mandate_id,
            "sii_to_send": False,
            "account_id": invoice_account_ids[0],
            "journal_id": journal_ids[0],
        }

        invoice_vals.update(invoice_o.onchange_partner_id(  # Get invoice default values
            cursor, uid, [], "out_invoice", partner_id).get("value", {})
        )
        invoice_vals.update({"payment_type": payment_type_id})

        invoice_id = invoice_o.create(cursor, uid, invoice_vals, context=context)
        invoice_o.button_reset_taxes(cursor, uid, [invoice_id])

        self.write(cursor, uid, lead.id, {"initial_invoice_id": invoice_id}, context=context)

        # open the invoice
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cursor)

        # fer un tipus de pagament especial per a la quota de soci i despres buscar una remesa
        # oberta o crearla de nou com fa generation a get_or_create_open_payment_order
        payment_mode_id = ir_model_o.get_object_reference(
            cursor, uid, "som_polissa_soci", "mode_pagament_socis"
        )[1]
        payment_mode_name = payment_mode_o.read(
            cursor, uid, payment_mode_id, ["name"], context=context
        )["name"]
        payment_order_id = payment_order_o.get_or_create_open_payment_order(
            cursor, uid, payment_mode_name, use_invoice=True, context=context
        )
        invoice_o.afegeix_a_remesa(cursor, uid, [invoice_id], payment_order_id)

    def get_or_create_payment_mandate(self, cursor, uid, partner_id, iban, purpose, context=None):
        if context is None:
            context = {}

        partner_o = self.pool.get("res.partner")
        mandate_o = self.pool.get("payment.mandate")

        partner = partner_o.read(cursor, uid, partner_id, ['address', 'name', 'vat'])
        search_params = [
            ('debtor_iban', '=', iban),
            ('debtor_vat', '=', partner['vat']),
            ('date_end', '=', False),
            ('reference', '=', 'res.partner,{}'.format(partner_id)),
            ('notes', '=', purpose),
        ]

        mandate_ids = mandate_o.search(cursor, uid, search_params)
        if mandate_ids:
            return mandate_ids[0]

        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        mandate_reference = "res.partner,{}".format(partner_id)
        mandate_scheme = "core"

        return mandate_o.create(cursor, uid, {
            "date": today,
            "reference": mandate_reference,
            "mandate_scheme": mandate_scheme,
            "signed": 1,
            "debtor_iban": iban.replace(" ", ""),
            "payment_type": "one_payment",
            'notes': purpose,
        })

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        seq_o = self.pool.get("ir.sequence")

        if vals.get("create_new_member"):
            vals['member_number'] = seq_o.get_next(cursor, uid, 'res.partner.soci')

        lead_id = super(GiscedataCrmLead, self).create(cursor, uid, vals, context=context)

        return lead_id

    def create_partner(self, cursor, uid, create_vals, crml_id, context=None):
        if context is None:
            context = {}

        member_o = self.pool.get("somenergia.soci")

        if context.get("create_member"):
            create_vals['ref'] = self.read(
                cursor, uid, crml_id, ["member_number"], context=context
            )["member_number"]

        if context.get("partner_representantive_id"):
            create_vals["representante_id"] = context["partner_representantive_id"]

        partner_id = super(GiscedataCrmLead, self).create_partner(
            cursor, uid, create_vals, crml_id, context=context)

        if context.get("create_member"):
            member_o.create_one_soci(cursor, uid, partner_id, context=context)

        return partner_id

    _columns = {
        "tipus_tarifa_lead": fields.selection(_tipus_tarifes_lead, "Tipus de tarifa del contracte"),
        "set_custom_potencia": fields.boolean("Personalitzar preus potència"),
        "preu_fix_energia_p1": fields.float("Preu Fix Energia P1", digits=(16, 6)),
        "preu_fix_energia_p2": fields.float("Preu Fix Energia P2", digits=(16, 6)),
        "preu_fix_energia_p3": fields.float("Preu Fix Energia P3", digits=(16, 6)),
        "preu_fix_energia_p4": fields.float("Preu Fix Energia P4", digits=(16, 6)),
        "preu_fix_energia_p5": fields.float("Preu Fix Energia P5", digits=(16, 6)),
        "preu_fix_energia_p6": fields.float("Preu Fix Energia P6", digits=(16, 6)),
        "preu_fix_potencia_p1": fields.float("Preu Fix Potència P1", digits=(16, 6)),
        "preu_fix_potencia_p2": fields.float("Preu Fix Potència P2", digits=(16, 6)),
        "preu_fix_potencia_p3": fields.float("Preu Fix Potència P3", digits=(16, 6)),
        "preu_fix_potencia_p4": fields.float("Preu Fix Potència P4", digits=(16, 6)),
        "preu_fix_potencia_p5": fields.float("Preu Fix Potència P5", digits=(16, 6)),
        "preu_fix_potencia_p6": fields.float("Preu Fix Potència P6", digits=(16, 6)),
        "member_number": fields.char('Número de sòcia', size=64),
        "initial_invoice_id": fields.many2one("account.invoice", "Factura de remesa inicial"),
        "create_new_member": fields.boolean("Sòcia de nova creació"),
        "member_quota_payment_type": fields.selection(
            _member_quota_payment_types, "Forma pagament quota sòcia"),
        "donation": fields.boolean("Donatiu voluntari"),
    }

    _defaults = {
        "tipus_tarifa_lead": lambda *a: "tarifa_existent",
        "set_custom_potencia": lambda *a: False,
        "donation": lambda *a: False,
    }


GiscedataCrmLead()
