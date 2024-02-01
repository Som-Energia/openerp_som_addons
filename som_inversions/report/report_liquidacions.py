from osv import osv
from yamlns import namespace as ns
import pooler
from datetime import datetime, timedelta
from report import report_sxw
from tools import config
from c2c_webkit_report import webkit_report


class AccountInvoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    def report_liquidacions_titols_data(self, cursor, uid, ids):
        inv = self.browse(cursor, uid, ids[0])
        data = ns()
        data.lines = []
        for line in inv.invoice_line:
            data.lines.append(
                ns(
                    date_ini=line.name.split(" ")[1],
                    date_end=line.name.split(" ")[3],
                    quantity=line.quantity,
                    interest_type=float(line.note.split(" ")[6].split("/")[0]) * 100,
                    generated_interests=line.price_subtotal,
                )
            )

        data.total = inv.amount_untaxed
        data.tax_lines = []
        for tax in inv.tax_line:
            data.tax_lines.append(ns(name=" ".join(tax.name.split(" ")[1:]), amount=tax.amount))

        data.to_pay_total = inv.amount_total
        data.partner_iban = inv.partner_bank.printable_iban

        data.somenergia = get_somenergia_partner_info(cursor, uid)
        data.year = (datetime.now() - timedelta(days=365)).year

        data.partner_name = inv.partner_id.name
        data.partner_vat = inv.partner_id.vat

        return data

    def report_liquidacions_data(self, cursor, uid, ids):
        inv = self.browse(cursor, uid, ids[0])
        data = ns()
        data.lines = []
        for line in inv.invoice_line:
            data.lines.append(
                ns(
                    date_ini=line.name.split(" ")[3],
                    date_end=line.name.split(" ")[6],
                    quantity=float(line.note.split("investmentInitialAmount: ")[1].split("\n")[0]),
                    interest_type=float(line.note.split("interestRate: ")[1].split("\n")[0]),
                    generated_interests=line.price_subtotal,
                )
            )

        data.total = inv.amount_untaxed
        data.tax_lines = []
        for tax in inv.tax_line:
            data.tax_lines.append(ns(name=" ".join(tax.name.split(" ")[1:]), amount=tax.amount))

        data.to_pay_total = inv.amount_total
        data.partner_iban = inv.partner_bank.printable_iban

        data.somenergia = get_somenergia_partner_info(cursor, uid)
        data.year = (datetime.now() - timedelta(days=365)).year

        data.partner_name = inv.partner_id.name
        data.partner_vat = inv.partner_id.vat

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


class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name, context=context)
        self.localcontext.update(
            {
                "cursor": cursor,
                "uid": uid,
                "addons_path": config["addons_path"],
            }
        )


webkit_report.WebKitParser(
    "report.liquidacions.interessos",
    "account.invoice",
    "som_inversions/report/report_liquidacions_interessos.mako",
    parser=report_webkit_html,
)

webkit_report.WebKitParser(
    "report.liquidacions.interessos.unificat",
    "res.partner",
    "som_inversions/report/report_liquidacions_interessos_unificat.mako",
    parser=report_webkit_html,
)

webkit_report.WebKitParser(
    "report.liquidacions.titols",
    "account.invoice",
    "som_inversions/report/report_liquidacions_titols.mako",
    parser=report_webkit_html,
)

webkit_report.WebKitParser(
    "report.retencions.interessos",
    "account.invoice",
    "som_inversions/report/report_retencions_interessos.mako",
    parser=report_webkit_html,
)

webkit_report.WebKitParser(
    "report.generationkwh.doc",
    "account.invoice",
    "som_inversions/report/report_generationkwh_doc.mako",
    parser=report_webkit_html,
)
