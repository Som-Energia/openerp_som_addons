from osv import osv
from yamlns import namespace as ns
import pooler
from osv.expression import OOQuery
from datetime import datetime, timedelta, date
from report import report_sxw
from tools import config
from c2c_webkit_report import webkit_report


class AccountInvoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    def report_retencions_data(self, cursor, uid, ids):
        invest_obj = self.pool.get("generationkwh.investment")
        inv = self.browse(cursor, uid, ids[0])
        data = ns()
        data.lang = inv.partner_id.lang
        data.somenergia = get_somenergia_partner_info(cursor, uid)
        data.year = inv.date_invoice.split("-")[0]
        data.type = inv.journal_id.code
        data.partner_name = inv.partner_id.name
        data.partner_vat = inv.partner_id.vat[2:]
        data.amount_untaxed = inv.amount_untaxed
        data.amount_tax = abs(inv.amount_tax)
        data.date_invoice = inv.date_invoice
        data.date_last_date_previous_year = "{}-12-31".format(data.year)

        data.balance = 0
        if data.type == "APO":
            search_params = [
                ("emission_id.type", "=", "apo"),
                ("member_id.partner_id.id", "=", inv.partner_id.id),
                ("purchase_date", "<=", data.date_last_date_previous_year),
                "|",
                ("last_effective_date", ">", data.date_last_date_previous_year),
                ("last_effective_date", "=", False),
            ]
            aportacions_member_ids = invest_obj.search(cursor, uid, search_params)
            aportacions_member = invest_obj.browse(cursor, uid, aportacions_member_ids)
            total_member_nshares = sum([item.nshares for item in aportacions_member])
            data.balance = total_member_nshares * gkwh.shareValue

        elif data.type == "TIT":
            aml_obj = self.pool.get("account.move.line")
            account_id = inv.partner_id.property_account_titols.id
            ids = aml_obj.search(cursor, uid, [("account_id", "=", account_id)])
            search_params = [
                ("id", "in", ids),
                ("move_id.period_id.special", "=", False),
                ("date", "<=", data.date_last_date_previous_year),
            ]

            aml_id = aml_obj.search(cursor, uid, search_params, order="id desc", limit=1)[0]
            data.balance = abs(aml_obj.read(cursor, uid, aml_id, ["balance"])["balance"])

        return data


AccountInvoice()


def get_somenergia_partner_info(cursor, uid):
    pool = pooler.get_pool(cursor.dbname)
    ResPartner = pool.get("res.partner")
    ResPartnerAdress = pool.get("res.partner.address")
    som_partner_id = 1  # ResPartner.search(cursor, uid, [('vat','=','ESF55091367')])
    som_partner = ResPartner.read(cursor, uid, som_partner_id, ["name", "vat", "address"])
    som_address = ResPartnerAdress.read(
        cursor, uid, som_partner["address"][0], ["street", "zip", "city"]
    )
    data = ns()
    data.address_city = som_address["city"]
    data.address_zip = som_address["zip"]
    data.address_street = som_address["street"]
    data.partner_name = som_partner["name"]
    data.partner_vat = som_partner["vat"]
    return data
