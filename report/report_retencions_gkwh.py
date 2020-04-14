# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
from generationkwh.isodates import isodate
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import logging


class GenerationkwhInvestment(osv.osv):
    _name = 'somenergia.soci'
    _inherit = 'somenergia.soci'

    def send_emails_to_investors_with_savings_in_year(self, cursor, uid, year=None):
        """
        Send email to the partners with retencions.rendiment.gkwh report
        attached to certificat_retencio_rendiment_generationkwh poweremail template.
        Only partners with generationkwh.investment investments that had saving at
        given year.
        """
        if year is None:
            raise Exception("Year must have a value")

        pool = pooler.get_pool(cursor.dbname)
        Investment = pool.get('generationkwh.investment')

        last_day = str(year) + '-12-31'

        all_investments_ids_in_year = Investment.search(cursor, uid, [('first_effective_date','<=', last_day)])
        if all_investments_ids_in_year is None:
            raise Exception("No investments found at year {}".format(year))

        members = []
        for invest_id in all_investments_ids_in_year:
            investment = Investment.read(cursor, uid, invest_id, ['member_id'])
            members.append(investment['member_id'][0])

        members = set(members)
        email_params = RetencionsSobreRendimentGenerationKwh.get_email_params(cursor, uid, self)

        for member_id in members:
            RetencionsSobreRendimentGenerationKwh.send_email(
                cursor, uid, self, member_id, email_params
            )
        return True

    def added_member_investment_in_year(self, cursor, uid, year=None):
        if year is None:
            raise Exception("Year must have a value")

    def generationkwh_amortization_data_as_dict(self, cursor, uid, ids):
        return dict(self.investmentAmortization_notificationData(cursor, uid, ids))

    def generationkwh_amortization_data(self, cursor, uid, ids):

        if not ids: raise Exception("No member provided")
        member_id = ids[0]

        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Accounts = pool.get('poweremail.core_accounts')
        Investment = pool.get('generationkwh.investment')
        ResPartner = pool.get('res.partner')
        ResPartnerAdress = pool.get('res.partner.address')
        partner_id = 1  # ResPartner.search(cursor, uid, [('vat','=','ESF55091367')])
        partner = ResPartner.read(cursor, uid, partner_id, ['name', 'vat', 'address'])
        address = ResPartnerAdress.read(cursor, uid, partner['address'][0], ['street', 'zip', 'city'])

        report.year = (datetime.now() - timedelta(days=365)).year

        accounts = Accounts.search(cursor, uid, [('name', 'ilike', 'Generation'), ('state', '=', 'approved')])

        if accounts:
            account_id = accounts[0]
            report.address_email = Accounts.read(cursor, uid, account_id, ['email_id'])['email_id']
        else:
            report.address_email = None

        investments = Investment.search(cursor, uid, [('emission_id.type', '=', 'genkwh'), ('member_id','=', member_id)])
        first_investment = Investment.browse(cursor, uid, investments[0])

        report.address_city = address['city']
        report.address_zip = address['zip']
        report.address_street = address['street']
        report.partner_name = partner['name']
        report.partner_vat = partner['vat']
        report.partner_address = partner['address']

        member_id = first_investment.member_id.id

        total_irpf_values = {}
        for investment_id in investments:
            if Investment.read(cursor, uid, investment_id, ['first_effective_date'])['first_effective_date'] is False:
                continue

            irpf_values = Investment.get_irpf_amounts(cursor, uid, investment_id , member_id, report.year)

            if 'total_irpf_saving' in total_irpf_values:
                total_irpf_values['total_irpf_saving'] += irpf_values['irpf_saving']
            else:
                total_irpf_values['total_irpf_saving'] = irpf_values['irpf_saving']

            if 'total_irpf_amount' in total_irpf_values:
                total_irpf_values['total_irpf_amount'] += irpf_values['irpf_amount']
            else:
                total_irpf_values['total_irpf_amount'] = irpf_values['irpf_amount']

        report.data_inici = date(report.year, 1, 1).isoformat()
        report.data_fi = date(report.year, 12, 31).isoformat()
        report.member_name = first_investment.member_id.partner_id.name
        report.member_vat = first_investment.member_id.partner_id.vat[2:]
        report.estalvi = total_irpf_values['total_irpf_saving']
        report.retencio = total_irpf_values['total_irpf_amount']
        report.language = first_investment.member_id.partner_id.lang

        return report

GenerationkwhInvestment()


class RetencionsSobreRendimentGenerationKwh():
    @staticmethod
    def get_email_params(cursor, uid, _object):
        """
        Return email from poweremail template
        """
        ir_model_data = _object.pool.get('ir.model.data')
        account_obj = _object.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = _object.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_generationkwh', 'certificat_retencio_rendiment_generationkwh'
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        template_name = 'Generation'

        if template.get(template_name):
            email_from = template.get('enforce_from_account')[0]

        if not email_from:
            email_from = account_obj.search(cursor, uid, [('name', 'ilike', template_name)])[0]

        email_params = dict({
            'email_from': email_from,
            'template_id': template_id
        })

        return email_params

    @staticmethod
    def send_email(cursor, uid, _object, member_id, email_params):
        logger = logging.getLogger('openerp.poweremail')

        try:
            wiz_send_obj = _object.pool.get('poweremail.send.wizard')
            ctx = {
                'active_ids': [member_id],
                'active_id': member_id,
                'template_id': email_params['template_id'],
                'src_model': 'somenergia.soci',
                'src_rec_ids': [member_id],
                'from': email_params['email_from'],
                'state': 'single',
                'priority': '0',
            }

            power_email_tmpl_obj = _object.pool.get('poweremail.templates')
            template = power_email_tmpl_obj.browse(cursor, uid, [email_params['template_id']])

            if template.report_template.context:
                ctx.update(eval(template.report_template.context))

            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            logger.info(
                'ERROR sending email to member {member}: {exc}'.format(
                    member=member_id,
                    exc=e
                )
            )
            return -1

# vim: et ts=4 sw=4