from osv import osv
from yamlns import namespace as ns
import pooler
import datetime
import generationkwh.investmentmodel as gkwh


class ResPartner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"

    def report_retencions_data(self, cursor, uid, ids, is_generationkwh=False):
        aeat193_record_obj = self.pool.get("l10n.es.aeat.mod193.record")
        investment_obj = self.pool.get("generationkwh.investment")
        partner = self.browse(cursor, uid, ids[0])

        data = ns()
        data.year = str(datetime.date.today().year - 1)
        aeat193_company_name = "APORTACIONS VOLUNTARIES" if not is_generationkwh else "GKWh"
        search_params = [
            ("partner_id", "=", ids[0]),
            ("report_id.company_name", "=", aeat193_company_name),
            ("fiscal_year_id.name", "=", data.year),
        ]
        aeat193_record_ids = aeat193_record_obj.search(
            cursor,
            uid,
            search_params,
            limit=1,
        )
        aeat193_record = aeat193_record_obj.browse(
            cursor,
            uid,
            aeat193_record_ids,
        )
        data.lang = partner.lang
        data.somenergia = get_somenergia_partner_info(cursor, uid)
        data.partner_name = partner.name
        data.partner_vat = partner.vat[2:]
        data.amount_untaxed = aeat193_record[0].amount_base if aeat193_record else 0
        data.amount_tax = abs(aeat193_record[0].amount_tax) if aeat193_record else 0
        data.date_last_date_previous_year = "{}-12-31".format(data.year)
        data.balance = 0
        if not is_generationkwh:
            search_params = [
                ("emission_id.type", "=", "apo"),
                ("member_id.partner_id.id", "=", ids[0]),
                ("purchase_date", "<=", data.date_last_date_previous_year),
                "|",
                ("last_effective_date", ">", data.date_last_date_previous_year),
                ("last_effective_date", "=", False),
            ]
            aportacions_member_ids = investment_obj.search(cursor, uid, search_params)
            aportacions_member = investment_obj.browse(cursor, uid, aportacions_member_ids)
            total_member_nshares = sum([item.nshares for item in aportacions_member])
            data.balance = total_member_nshares * gkwh.shareValue

        return data


ResPartner()


def get_somenergia_partner_info(cursor, uid):
    pool = pooler.get_pool(cursor.dbname)
    ResPartner = pool.get("res.partner")
    ResPartnerAdress = pool.get("res.partner.address")
    som_partner_id = 1
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
