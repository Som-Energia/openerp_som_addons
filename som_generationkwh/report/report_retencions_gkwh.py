# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
from generationkwh.isodates import isodate
from dateutil.relativedelta import relativedelta

class GenerationkwhInvestment(osv.osv):
    _name = 'generationkwh.investment'
    _inherit = 'generationkwh.investment'

    def generationkwh_amortization_data_as_dict(self, cursor, uid, ids):
        return dict(self.investmentAmortization_notificationData(cursor, uid, ids))

    def generationkwh_amortization_data(self, cursor, uid, ids):
        
        investment_id = ids[0]
        if not ids: raise Exception("No investments provided")

        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Investment = pool.get('generationkwh.investment')
        ResPartner = pool.get('res.partner')
        ResPartnerAdress = pool.get('res.partner.address')
        partner_id = 1#ResPartner.search(cursor, uid, [('vat','=','ESF55091367')])
        address = ResPartnerAdress.read(cursor, uid, partner['address'][0], ['street','zip','city','email'])
        partner = ResPartner.read(cursor, uid, partner_id, ['name','vat','address'])
        report.year = (datetime.now() - timedelta(days=365)).year


        investment = Investment.browse(cursor, uid, investment_id)
        report.address_city = address['city']
        report.address_zip = address['zip']
        report.address_street = address['street']
        report.address_email = address['email']
        report.partner_name = partner['name']
        report.partner_vat = partner['vat']
        report.partner_address = partner['address']

        member_id = investment.member_id.id
        irpf_values = Investment.get_irpf_amounts(cursor, uid, investment_id , member_id, report.year)

        report.data_inici = date(report.year, 1, 1).isoformat()
        report.data_fi = date(report.year, 12, 31).isoformat()
        report.member_name = investment.member_id.partner_id.name
        report.member_vat = investment.member_id.partner_id.vat[2:]
        report.estalvi = irpf_values['irpf_saving']
        report.retencio = irpf_values['irpf_amount']
        report.language = investment.member_id.partner_id.lang

        return report

GenerationkwhInvestment()
# vim: et ts=4 sw=4