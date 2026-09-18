# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import fields, osv
from tools.translate import _
import datetime
import netsvc

ACC_CODE_WIDTH = 12
MEMBER_FEE_PURPOSE = "QUOTA SOCI"


class ResPartner(osv.osv):
    """Modifiquem res_partner per poder crear un compte comptable a partir del
    seu codi (ref)."""

    _name = "res.partner"
    _inherit = "res.partner"

    def create_account(
        self, cursor, uid, ids, acc_code, acc_type, user_type, code_gen, context=None
    ):
        """Mètode genèric per crear comptes comptables específics per clients"""
        if not context:
            context = {}
        parent = None
        res = {}
        account_obj = self.pool.get("account.account")
        search_params = [("code", "=", acc_code)]
        account = account_obj.search(cursor, uid, search_params)
        if account:
            parent = account[0]
        else:
            raise osv.except_osv(_("Error"), _(u"No s'ha trobat el compte pare"))
        ut_obj = self.pool.get("account.account.type")
        search_params = [("code", "=", user_type)]
        usertype = ut_obj.search(cursor, uid, search_params)
        for partner in self.browse(cursor, uid, ids):
            account_code = code_gen(cursor, uid, partner.id, parent, context)
            account_code = account_code[str(partner.id)]
            # comprovem que no existeixi ja el compte primer
            search_params = [("code", "=", account_code)]
            found = account_obj.search(cursor, uid, search_params)
            if found:
                res[str(partner.id)] = found[0]
            else:
                vals = {
                    "name": partner.name,
                    "parent_id": parent,
                    "code": account_code,
                    "user_type": usertype[0],
                    "type": acc_type,
                    "reconcile": 1,
                }
                res[str(partner.id)] = account_obj.create(cursor, uid, vals, context)
        return res

    def generate_acc_code_43(self, cursor, uid, ids, parent_id=None, context=None):
        """Mètode per generar el codi del nou compte pel soci a Clientes 4300."""
        if not context:
            context = {}
        res = {}
        account_obj = self.pool.get("account.account")
        if not parent_id:  # si no hi ha parent, malament.
            return res
        if not isinstance(ids, list):
            ids = [ids]
        parent = account_obj.read(cursor, uid, parent_id, ["code", "parent_id"])
        grandparent = account_obj.read(cursor, uid, parent["parent_id"][0], ["code"])
        parent_prefix = grandparent["code"]
        for partner in self.browse(cursor, uid, ids):
            base = partner.ref
            if partner.ref.startswith("S"):
                base = partner.ref.replace("S", "1", 1)
            if partner.ref.startswith("T"):
                base = partner.ref.replace("T", "2", 1)
            # netejem caràcters no numèrics
            if not base.isdigit():
                base = "".join([c for c in base if c.isdigit()])
            padding = "0" * (ACC_CODE_WIDTH - len(parent_prefix) - len(base))
            res[str(partner.id)] = "%s%s%s" % (parent_prefix, padding, base)
        return res

    def generate_acc_code_410(self, cursor, uid, ids, parent_id=None, context=None):
        """Mètode que genera el codi pel compte comptable 410*."""
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        prefix = "4100"
        for partner in self.browse(cursor, uid, ids, context):
            ref = "".join([a for a in partner.ref if a.isdigit()])
            padding = "0" * (ACC_CODE_WIDTH - len(prefix) - len(ref))
            res[str(partner.id)] = "%s%s%s" % (prefix, padding, ref)
        return res

    def generate_acc_code_163(self, cursor, uid, ids, parent_id=None, context=None):
        """Mètode que genera el codi pel compte comptable 163*."""
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        prefix = "163"
        for partner in self.browse(cursor, uid, ids, context):
            ref = "".join([a for a in partner.ref if a.isdigit()])
            padding = "0" * (ACC_CODE_WIDTH - len(prefix) - len(ref))
            res[str(partner.id)] = "%s%s%s" % (prefix, padding, ref)
        return res

    def generate_acc_code_1714(self, cursor, uid, ids, parent_id=None, context=None):
        """Mètode que genera el codi pel compte comptable 1714*."""
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        prefix = "1714"
        for partner in self.browse(cursor, uid, ids, context):
            ref = "".join([a for a in partner.ref if a.isdigit()])
            padding = "0" * (ACC_CODE_WIDTH - len(prefix) - len(ref))
            res[str(partner.id)] = "%s%s%s" % (prefix, padding, ref)
        return res

    def generate_acc_code_1635(self, cursor, uid, ids, parent_id=None, context=None):
        """Mètode que genera el codi pel compte comptable 1635*."""
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        res = {}
        prefix = "1635"
        for partner in self.browse(cursor, uid, ids, context):
            ref = "".join([a for a in partner.ref if a.isdigit()])
            padding = "0" * (ACC_CODE_WIDTH - len(prefix) - len(ref))
            res[str(partner.id)] = "%s%s%s" % (prefix, padding, ref)
        return res

    def create_account_43(self, cursor, uid, ids, context=None):
        """Mètode que crea l'account_account 43* corresponent al partner"""
        if not context:
            context = {}
        return self.create_account(
            cursor,
            uid,
            ids,
            "4300",
            "receivable",
            "terceros - rec",
            self.generate_acc_code_43,
            context,
        )

    def create_account_410(self, cursor, uid, ids, context=None):
        """Mètode que crea l'account_account 410* corresponent al partner"""
        if not context:
            context = {}
        return self.create_account(
            cursor,
            uid,
            ids,
            "4100",
            "payable",
            "terceros - pay",
            self.generate_acc_code_410,
            context,
        )

    def create_account_163(self, cursor, uid, ids, context=None):
        """Mètode que crea l'account_account 163* corresponent al partner"""
        if not context:
            context = {}
        return self.create_account(
            cursor, uid, ids, "163", "other", "capital", self.generate_acc_code_163, context
        )

    def create_account_1714(self, cursor, uid, ids, context=None):
        """Mètode que crea l'account_account 163* corresponent al partner"""
        if not context:
            context = {}
        return self.create_account(
            cursor, uid, ids, "1714", "other", "capital", self.generate_acc_code_1714, context
        )

    def create_account_1635(self, cursor, uid, ids, context=None):
        """Mètode que crea l'account_account 163* corresponent al partner"""
        if not context:
            context = {}
        return self.create_account(
            cursor, uid, ids, "1635", "other", "capital", self.generate_acc_code_1635, context
        )

    def button_assign_acc_43(self, cursor, uid, ids, context=None):
        """Mètode per ser cridat des del botó."""
        if not context:
            context = {}
        res = self.create_account_43(cursor, uid, ids, context)
        for partner_id in res:
            self.write(
                cursor, uid, int(partner_id), {"property_account_receivable": res[partner_id]}
            )
        return True

    def button_assign_acc_410(self, cursor, uid, ids, context=None):
        """Mètode per ser cridat des del botó."""
        if not context:
            context = {}
        res = self.create_account_410(cursor, uid, ids, context)
        for partner_id in res:
            self.write(
                cursor, uid, int(partner_id), {"property_account_liquidacio": res[partner_id]}
            )
        return True

    def button_assign_acc_163(self, cursor, uid, ids, context=None):
        """Mètode per ser cridat des del botó."""
        if not context:
            context = {}
        gen_ids = []
        for partner in self.read(cursor, uid, ids, ["property_account_aportacions"]):
            if not partner["property_account_aportacions"]:
                gen_ids.append(partner["id"])
        if gen_ids:
            aa_obj = self.pool.get("account.account")
            ag_id = aa_obj.search(cursor, uid, [("code", "=", "163000000000")])
            if ag_id:
                for partner in self.browse(cursor, uid, ids):
                    self.write(
                        cursor, uid, int(partner.id), {"property_account_aportacions": ag_id[0]}
                    )
            else:
                return False
        return True

    def button_assign_acc_1714(self, cursor, uid, ids, context=None):
        """Mètode per ser cridat des del botó."""
        if not context:
            context = {}
        res = self.create_account_1714(cursor, uid, ids, context)
        for partner_id in res:
            self.write(cursor, uid, int(partner_id), {"property_account_titols": res[partner_id]})
        return True

    def button_assign_acc_1635(self, cursor, uid, ids, context=None):
        """Mètode per ser cridat des del botó."""
        if not context:
            context = {}
        aa_obj = self.pool.get("account.account")
        ag_id = aa_obj.search(cursor, uid, [("code", "=", "163500000000")])
        if ag_id:
            for partner in self.browse(cursor, uid, ids):
                self.write(cursor, uid, int(partner.id), {"property_account_gkwh": ag_id[0]})
            return True
        else:
            return False

    def create_member_fee_payment(
            self, cursor, uid, partner_id, iban, member_number, invoice_number,
            context=None):
        if context is None:
            context = {}

        iban = iban.replace(" ", "")

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

        payment_mode_id = ir_model_o.get_object_reference(
            cursor, uid, "som_partner_account", "mode_pagament_socis_factura"
        )[1]
        payment_mode = payment_mode_o.read(
            cursor, uid, payment_mode_id, ["name", "sepa_creditor_code"], context=context
        )

        mandate_id = mandate_o.get_or_create_payment_mandate(
            cursor,
            uid,
            partner_id,
            iban,
            MEMBER_FEE_PURPOSE,
            creditor_code=payment_mode["sepa_creditor_code"],
            payment_type="one_payment",
            context=context,
        )
        socia_fee_amount = conf_o.get(cursor, uid, "socia_member_fee_amount", "100")
        euro_id = currency_o.search(cursor, uid, [("code", "=", "EUR")])[0]
        invoice_account_id = account_o.search(
            cursor, uid, [("code", "=", "100000000000")], context=context
        )[0]
        bank_id = bank_o.search(
            cursor, uid, [("iban", "=", iban), ("partner_id", "=", partner_id)],
            limit=1, context=context
        )[0]
        journal_id = journal_o.search(
            cursor, uid, [("code", "=", "SOCIS")], context=context
        )[0]
        payment_type_id = payment_type_o.search(
            cursor, uid, [("code", "=", "TRANSFERENCIA_CSB")], context=context
        )[0]
        invoice_vals = {
            "number": invoice_number,
            "partner_id": partner_id,
            "type": "out_invoice",
            "invoice_line": [(0, 0, {
                "name": MEMBER_FEE_PURPOSE,
                "account_id": invoice_account_id,
                "price_unit": socia_fee_amount,
                "quantity": 1,
                "uom_id": 1,
                "company_currency_id": euro_id,
            })],
            "origin_date_invoice": datetime.datetime.today().strftime("%Y-%m-%d"),
            "date_invoice": datetime.datetime.today().strftime("%Y-%m-%d"),
            "mandate_id": mandate_id,
            "sii_to_send": False,
            "account_id": invoice_account_id,
            "journal_id": journal_id,
        }
        invoice_vals.update(invoice_o.onchange_partner_id(
            cursor, uid, [], "out_invoice", partner_id).get("value", {})
        )
        invoice_vals.update({
            "payment_type": payment_type_id,
            "partner_bank": bank_id,
            "sii_to_send": False,
        })

        invoice_id = invoice_o.create(cursor, uid, invoice_vals, context=context)
        invoice_o.button_reset_taxes(cursor, uid, [invoice_id])

        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, "account.invoice", invoice_id, "invoice_open", cursor)
        invoice_o.write(cursor, uid, [invoice_id], {"sii_to_send": False}, context=context)

        payment_order_id = payment_order_o.get_or_create_open_payment_order(
            cursor, uid, payment_mode["name"], use_invoice=True,
            context={"type": "receivable"}
        )
        invoice_o.afegeix_a_remesa(cursor, uid, [invoice_id], payment_order_id, context=context)

        payment_line_ids = payment_line_o.search(
            cursor, uid,
            [
                ("partner_id", "=", partner_id),
                ("communication", "=", invoice_number),
                ("order_id", "=", payment_order_id),
            ],
            context=context
        )
        payment_line_o.write(
            cursor, uid, payment_line_ids, {"name": member_number}, context=context
        )
        return invoice_id

    def become_member(self, cursor, uid, id, context=None):
        if not context:
            context = {}

        imd_obj = self.pool.get("ir.model.data")
        soci_obj = self.pool.get("somenergia.soci")
        ir_seq = self.pool.get("ir.sequence")
        soci_cat = imd_obj._get_obj(cursor, uid, "som_partner_account", "res_partner_category_soci")

        # Assign Member category and ref code
        partner_vals = {}
        partner = self.read(cursor, uid, id, ["ref", "category_id"])
        if soci_cat.id not in partner["category_id"]:
            partner_vals["category_id"] = [(4, soci_cat.id)]

        partner_vals['ref'] = context.get('force_ref', ir_seq.get(cursor, uid, "res.partner.soci"))
        self.write(cursor, uid, partner["id"], partner_vals)

        # Create Member instance
        soci_ids = soci_obj.search(
            cursor,
            uid,
            [
                ("partner_id", "=", partner["id"]),
            ],
            context={"active_test": False},
        )

        if soci_ids:
            soci_id = soci_ids[0]
            soci = soci_obj.read(
                cursor,
                uid,
                soci_id,
                [
                    "data_baixa_soci",
                    "comment",
                ],
            )
            newcomment = (
                (
                    _(
                        "{today:%Y-%m-%d} " "Donat d'alta quan estava de baixa des de {dropoutdate}"
                    ).format(
                        today=datetime.date.today(),
                        dropoutdate=soci["data_baixa_soci"],
                    )
                )
                if soci["data_baixa_soci"]
                else ""
            )

            comment = "\n".join([x for x in (soci["comment"], newcomment) if x])

            soci_obj.write(
                cursor,
                uid,
                soci_id,
                dict(
                    active=True,
                    data_baixa_soci=False,
                    baixa=False,
                    comment=comment,
                ),
            )

        if not soci_ids:
            context['mailchimp_from'] = 'become_member: partner_id {}'.format(partner["id"])
            soci_ids = [soci_obj.create_one_soci(cursor, uid, id, context)]

        return soci_ids[0]

    def adopt_contracts_as_member(self, cursor, uid, partner_id, context=None):
        contract_obj = self.pool.get("giscedata.polissa")
        contract_ids = contract_obj.search(
            cursor,
            uid,
            [
                "|",
                ("titular", "=", partner_id),
                ("pagador", "=", partner_id),
            ],
        )
        adopted_ids = []
        for contract_id in contract_ids:
            contract = contract_obj.read(cursor, uid, contract_id, ["pagador", "titular", "soci"])
            if contract["soci"]:
                if contract["soci"][0] == contract["pagador"][0]:
                    continue
                if contract["soci"][0] == contract["titular"][0]:
                    continue

            adopted_ids.append(contract_id)
            contract_obj.write(
                cursor,
                uid,
                contract_id,
                {
                    "soci": partner_id,
                },
            )

        return adopted_ids

    def button_assign_soci_seq(self, cursor, uid, ids, context=None):
        """Mètode per ser cridat des de botó.
        Assigna un nou codi de seqüència de soci al ref del partner
        en cas de no tenir-ne.
        """
        if not isinstance(ids, list):
            ids = [ids]

        for id in ids:
            self.become_member(cursor, uid, id)
            self.adopt_contracts_as_member(cursor, uid, id)

    _columns = {
        "property_account_aportacions": fields.property(
            "account.account",
            type="many2one",
            relation="account.account",
            string="Compte aportacions",
            method=True,
            view_load=True,
            domain=[("type", "=", "other")],
            help="Aquest és el compte on s'apuntaran les aportacions",
            required=False,
            readonly=True,
        ),
        "property_account_liquidacio": fields.property(
            "account.account",
            type="many2one",
            relation="account.account",
            string="Compte liquidacions",
            method=True,
            view_load=True,
            domain=[("type", "=", "payable")],
            help="Aquest és el compte on s'apuntaran les liquidacions " "d'aportacions",
            required=False,
            readonly=True,
        ),
        "property_account_titols": fields.property(
            "account.account",
            type="many2one",
            relation="account.account",
            string="Compte títols",
            method=True,
            view_load=True,
            domain=[("type", "=", "other")],
            help="Aquest és el compte on s'apuntaran la compra de títols",
            required=False,
            readonly=True,
        ),
        "property_account_gkwh": fields.property(
            "account.account",
            type="many2one",
            relation="account.account",
            string="Compte Generation kWh",
            method=True,
            view_load=True,
            domain=[("type", "=", "other")],
            help="Aquest és el compte on s'apuntarà el préstec generation kWh",
            required=False,
            readonly=True,
        ),
    }


ResPartner()
