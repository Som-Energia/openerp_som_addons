# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _
import datetime

ACC_CODE_WIDTH = 12


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
            soci_ids = [soci_obj.create_one_soci(cursor, uid, partner["id"])]

        soci = soci_obj.browse(cursor, uid, soci_ids[0])
        soci.subscriu_socia_mailchimp_async(cursor, uid, soci_ids[0], context=context)
        self.arxiva_client_mailchimp_async(cursor, uid, id, context=context)

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
