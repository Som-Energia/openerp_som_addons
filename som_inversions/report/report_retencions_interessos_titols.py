from osv import osv
from yamlns import namespace as ns
import pooler
import datetime


class ResPartner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def report_retencions_data(self, cursor, uid, ids):
        aeat193_record_obj = self.pool.get('l10n.es.aeat.mod193.record')
        partner = self.browse(cursor, uid, ids[0])
        data = ns()
        data.year = str(datetime.date.today().year - 1)
        import pudb; pu.db

        search_params = [
            ('partner_id', '=', ids[0]),
            ('report_id.company_name', '=', 'TITOLS'),
            ('fiscal_year_id.name', '=', data.year),
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
        data.date_last_date_previous_year = '{}-12-31'.format(data.year)
        data.balance = 0

        return data


ResPartner()


def get_somenergia_partner_info(cursor, uid):
    pool = pooler.get_pool(cursor.dbname)
    ResPartner = pool.get('res.partner')
    ResPartnerAdress = pool.get('res.partner.address')
    som_partner_id = 1
    som_partner = ResPartner.read(
        cursor, uid, som_partner_id, ['name', 'vat', 'address'])
    som_address = ResPartnerAdress.read(
        cursor, uid, som_partner['address'][0], ['street', 'zip', 'city'])
    data = ns()
    data.address_city = som_address['city']
    data.address_zip = som_address['zip']
    data.address_street = som_address['street']
    data.partner_name = som_partner['name']
    data.partner_vat = som_partner['vat']
    return data
