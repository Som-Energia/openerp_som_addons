from osv import osv
from yamlns import namespace as ns
import pooler
from datetime import datetime, timedelta


class ResPartner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def report_liquidacions_unificat_data(self, cursor, uid, ids):
        if isinstance(ids, list):
            ids = ids[0]
        partner = self.browse(cursor, uid, ids)
        current_year = datetime.today().year
        inv_obj = self.pool.get('account.invoice')
        search_params = [('partner_id', '=', ids),
                         ('date_invoice', '>=', '{}-01-01'.format(current_year)),
                         ('date_invoice', '<=', '{}-12-31'.format(current_year)),
                         ('type', '=', 'in_invoice'),
                         ('number', 'ilike', '%INT{}'.format(current_year)),
                         '|',
                         ('origin', 'ilike', 'APO%'),
                         ('origin', 'ilike', 'INV%'),
                         ]
        inv_ids = inv_obj.search(cursor, uid, search_params)
        invoices = inv_obj.browse(cursor, uid, inv_ids)
        data = {}
        data['invoices'] = {}

        for invoice in invoices:
            data['invoices'][invoice.origin] = {}
            data['invoices'][invoice.origin]['number'] = invoice.number
            data['invoices'][invoice.origin]['name'] = invoice.origin
            data['invoices'][invoice.origin]['amount_untaxed'] = invoice.amount_untaxed
            data['invoices'][invoice.origin]['tax_lines'] = []
            data['invoices'][invoice.origin]['lines'] = []
            for tax in invoice.tax_line:
                data['invoices'][invoice.origin]['tax_lines'].append(ns(
                    name=' '.join(tax.name.split(' ')[1:]),
                    amount=tax.amount
                ))

            data['invoices'][invoice.origin]['to_pay_total'] = invoice.amount_total
            data['invoices'][invoice.origin]['partner_iban'] = invoice.partner_bank.printable_iban

            for line in invoice.invoice_line:
                data['invoices'][invoice.origin]['lines'].append(ns(
                    date_ini=line.name.split(' ')[3],
                    date_end=line.name.split(' ')[6],
                    quantity=float(line.note.split(
                        'investmentInitialAmount: ')[1].split('\n')[0]),
                    interest_type=float(line.note.split(
                        'interestRate: ')[1].split('\n')[0]),
                    generated_interests=line.price_subtotal,
                ))
        data['partner_name'] = partner.name
        data['partner_vat'] = partner.vat

        data['somenergia'] = get_somenergia_partner_info(cursor, uid)
        data['year'] = (datetime.now() - timedelta(days=365)).year
        return data


ResPartner()


def get_somenergia_partner_info(cursor, uid):
    pool = pooler.get_pool(cursor.dbname)
    ResPartner = pool.get('res.partner')
    ResPartnerAdress = pool.get('res.partner.address')
    som_partner_id = 1  # ResPartner.search(cursor, uid, [('vat','=','ESF55091367')])
    som_partner = ResPartner.read(cursor, uid, som_partner_id, ['name', 'vat', 'address'])
    som_address = ResPartnerAdress.read(
        cursor, uid, som_partner['address'][0], ['street', 'zip', 'city'])
    data = {}
    data['address_city'] = som_address['city']
    data['address_zip'] = som_address['zip']
    data['address_street'] = som_address['street']
    data['partner_name'] = som_partner['name']
    data['partner_vat'] = som_partner['vat']

    return data
