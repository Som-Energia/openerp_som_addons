# -*- coding: utf-8 -*-
from datetime import datetime
from osv import fields, osv
import netsvc
from oorq.decorators import job

from base_extended_som.res_partner import GENDER_SELECTION


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

        member_id = partner_o.search(
            cursor, uid, [("ref", "=", member_number)], limit=1
        )

        if not member_id:
            raise osv.except_osv(
                "Error - Sòcia no trobada",
                "Prova de posar el número {} amb la lletra i els zeros".format(member_number),
            )

        values["soci"] = member_id[0]
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
        if not set_custom_potencia:
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

        partner_o = self.pool.get("res.partner")

        res = super(GiscedataCrmLead, self).create_entity_titular(
            cursor, uid, crml_id, context=context
        )

        lead = self.browse(cursor, uid, crml_id, context=context)
        values = {}

        # We set again the lang because if it existed before, the base code dont write it
        if lead.lang:
            values["lang"] = lead.lang

        rep_id = self._create_or_get_representative(
            cursor, uid, lead.persona_firmant_vat, lead.persona_nom, lead.lang, context=context
        )
        if rep_id:
            values["representante_id"] = rep_id

        if lead.create_new_member:
            # become_member will keep the member number we set here
            context["force_ref"] = lead.member_number
            values["date"] = datetime.today().strftime("%Y-%m-%d")
            partner_o.write(cursor, uid, lead.partner_id.id, values, context=context)
            partner_o.become_member(cursor, uid, lead.partner_id.id, context=context)
            partner_o.adopt_contracts_as_member(cursor, uid, lead.partner_id.id, context=context)
        elif values:
            partner_o.write(cursor, uid, lead.partner_id.id, values, context=context)

        return res

    def create_partner(self, cursor, uid, create_vals, crml_id, context=None):
        if context is None:
            context = {}

        lead = self.browse(cursor, uid, crml_id)
        if lead.titular_number:
            create_vals['ref'] = lead.titular_number

        create_vals["gender"] = lead.gender
        create_vals["birthdate"] = lead.birthdate
        create_vals["referral_source"] = lead.referral_source

        partner_id = super(GiscedataCrmLead, self).create_partner(
            cursor, uid, create_vals, crml_id, context=context)

        return partner_id

    def _create_or_get_representative(self, cursor, uid, vat, name, lang, context=None):
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
                values = {
                    "vat": vat,
                    "name": name,
                }
                if lang:
                    values["lang"] = lang
                representative_id = partner_o.create(cursor, uid, values, context=context)
        return representative_id

    def create_entity_iban(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}

        res = super(GiscedataCrmLead, self).create_entity_iban(
            cursor, uid, crml_id, context=context
        )

        lead = self.browse(cursor, uid, crml_id, context=context)
        if lead.create_new_member and lead.member_quota_payment_type == 'remesa':
            self.create_entity_member_bank_payment(cursor, uid, crml_id, context=context)

        return res

    def create_entity_member_bank_payment(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}

        invoice_o = self.pool.get("account.invoice")
        account_o = self.pool.get("account.account")
        journal_o = self.pool.get("account.journal")
        payment_type_o = self.pool.get("payment.type")
        payment_mode_o = self.pool.get("payment.mode")
        payment_order_o = self.pool.get("payment.order")
        payment_line_o = self.pool.get("payment.line")
        mandate_o = self.pool.get("payment.mandate")
        bank_o = self.pool.get("res.partner.bank")
        currency_o = self.pool.get("res.currency")
        conf_o = self.pool.get("res.config")
        ir_model_o = self.pool.get("ir.model.data")

        lead = self.browse(cursor, uid, crml_id, context=context)

        if lead.initial_invoice_id:
            raise osv.except_osv('Error', 'Ja existeix una factura de remesa inicial')

        partner_id = lead.partner_id.id
        mandate_id = mandate_o.get_or_create_payment_mandate(
            cursor, uid, partner_id, lead.iban, _MEMBER_FEE_PURPOSE,
            payment_type="one_payment", context=context
        )

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
        bank_id = bank_o.search(
            cursor, uid,
            [("iban", "=", lead.iban), ("partner_id", "=", lead.partner_id.id)],
            limit=1, context=context
        )[0]
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
        invoice_vals.update({"partner_bank": bank_id})

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
            cursor, uid, payment_mode_name, use_invoice=True, context={'type': 'receivable'}
        )
        invoice_o.afegeix_a_remesa(cursor, uid, [invoice_id], payment_order_id, context=context)

        # set the member number as the payment line name
        invoice = invoice_o.browse(cursor, uid, invoice_id)
        payment_line_id = payment_line_o.search(
            cursor, uid,
            [
                ("partner_id", "=", partner_id),
                ("communication", "=", invoice.number),
                ("order_id", "=", payment_order_id),
            ],
            context=context
        )
        payment_line_o.write(
            cursor, uid, payment_line_id, {"name": lead.member_number}, context=context)

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        seq_o = self.pool.get("ir.sequence")

        # We assing here the new numbers to show it in the contract to be signed
        if vals.get("create_new_member"):
            vals["member_number"] = seq_o.get_next(cursor, uid, "res.partner.soci")
        elif context.get("sponsored_titular"):
            vals["titular_number"] = seq_o.get_next(cursor, uid, "res.partner.titular")

        lead_id = super(GiscedataCrmLead, self).create(cursor, uid, vals, context=context)

        return lead_id

    def button_send_mail(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        lead_id = context["active_id"]
        self._send_mail(cr, uid, lead_id, context=context)

    @job(queue="poweremail_sender")
    def _send_mail_async(self, cr, uid, lead_id, context=None):
        self._send_mail(cr, uid, lead_id, context=context)

    def _send_mail(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        ir_model_o = self.pool.get('ir.model.data')
        template_o = self.pool.get('poweremail.templates')

        lead = lead_o.read(cr, uid, lead_id, ['create_new_member', 'polissa_id'], context=context)

        template_name = "email_contracte_esborrany"
        if lead["create_new_member"]:
            template_name = "email_contracte_esborrany_nou_soci"
        template_id = ir_model_o.get_object_reference(cr, uid, 'som_polissa_soci', template_name)[1]

        polissa_id = lead["polissa_id"][0]
        from_id = template_o.read(cr, uid, template_id)['enforce_from_account'][0]

        wiz_send_obj = self.pool.get("poweremail.send.wizard")
        context.update({
            "active_ids": [polissa_id],
            "active_id": polissa_id,
            "template_id": template_id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [polissa_id],
            "from": from_id,
            "state": "single",
            "priority": "0",
        })

        params = {"state": "single", "priority": "0", "from": context["from"]}
        wiz_id = wiz_send_obj.create(cr, uid, params, context)
        return wiz_send_obj.send_mail(cr, uid, [wiz_id], context)

    _columns = {
        "tipus_tarifa_lead": fields.selection(_tipus_tarifes_lead, "Tipus de tarifa del contracte"),
        "set_custom_potencia": fields.boolean("Sobreescriure preus potència"),
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
        "titular_number": fields.char('Número de titular (apadrinada)', size=64),
        "initial_invoice_id": fields.many2one("account.invoice", "Factura de remesa inicial"),
        "create_new_member": fields.boolean("Sòcia de nova creació"),
        "member_quota_payment_type": fields.selection(
            _member_quota_payment_types, "Forma pagament quota sòcia"),
        "donation": fields.boolean("Donatiu voluntari"),
        "referral_source": fields.char("Com ens ha conegut", size=255),
        "birthdate": fields.date("Data de naixement"),
        "gender": fields.selection(GENDER_SELECTION, "Gènere"),
        "comercial_info_accepted": fields.boolean("Accepta informació comercial (SomServeis)"),
        "crm_lead_id": fields.integer("ID del lead al CRM"),
    }

    _defaults = {
        "tipus_tarifa_lead": lambda *a: "tarifa_existent",
        "set_custom_potencia": lambda *a: False,
        "donation": lambda *a: False,
        "comercial_info_accepted": lambda *a: False,
        "crm_lead_id": lambda *a: 0,
    }


GiscedataCrmLead()
