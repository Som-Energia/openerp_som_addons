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

        def get_amortitzacions_any_en_curs_factures(member_items, partner_id):
            current_year = int(data.year) + 1
            start_date = "{}-01-01".format(current_year)

            investment_origins = []
            for item in member_items:
                if item.name:
                    investment_origins.append(item.name)

            if not investment_origins:
                return 0.0

            account_invoice_obj = self.pool.get('account.invoice')
            invoice_search_params = [
                ("partner_id", "=", partner_id),
                ("date_invoice", ">=", start_date),
                ("state", "in", ["open", "paid"]),
                ("origin", "in", investment_origins),
                "|",
                ("name", "ilike", "%-AMOR%"),
                ("name", "ilike", "%-DES%"),
            ]
            invoice_ids = account_invoice_obj.search(cursor, uid, invoice_search_params)

            amortitzacions = 0.0
            if invoice_ids:
                for invoice in account_invoice_obj.browse(cursor, uid, invoice_ids):
                    for line in invoice.invoice_line:
                        if line.product_id and line.product_id.default_code != gkwh.irpfProductCode:
                            amortitzacions += abs(line.price_subtotal)
            return amortitzacions

        if is_generationkwh:
            search_params = [
                ("emission_id.type", "=", "genkwh"),
                ("member_id.partner_id.id", "=", ids[0]),
                ("purchase_date", "<=", data.date_last_date_previous_year),
                "|",
                ("last_effective_date", ">", data.date_last_date_previous_year),
                ("last_effective_date", "=", False),
            ]
            gkwh_member_ids = investment_obj.search(cursor, uid, search_params)
            gkwh_member = investment_obj.browse(cursor, uid, gkwh_member_ids)
            total_remaining = sum(
                [(item.nshares * gkwh.shareValue) - item.amortized_amount for item in gkwh_member])
            amortitzacions_any_en_curs = get_amortitzacions_any_en_curs_factures(
                gkwh_member, ids[0])
            data.balance = total_remaining + amortitzacions_any_en_curs
        else:
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
            total_remaining = sum(
                [(item.nshares * gkwh.shareValue) - item.amortized_amount for item in aportacions_member])  # noqa: E501
            amortitzacions_any_en_curs = get_amortitzacions_any_en_curs_factures(
                aportacions_member, ids[0])
            data.balance = total_remaining + amortitzacions_any_en_curs

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
