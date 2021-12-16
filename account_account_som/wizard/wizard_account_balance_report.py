# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
import wizard
import time
from account_financial_report.utils import account_balance_utils as utils
from tools.translate import _
from osv import osv, fields



excel_fields = {
    'name': {'string': 'Fitxer Excel', 'type': 'char'},
    'file': {'string': 'Fitxer Excel', 'type': 'binary'}
}

excel_form = '''<?xml version="1.0"?>
<form string="Excel">
    <field name="file" colspan="4"/>
</form>'''

class WizardAccountBalanceReport(osv.osv_memory):

    _name = 'wizard.account.balance.report'

    def _get_defaults(self, cr, uid, data, context={}):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            company_id = user.company_id.id
        else:
            company_id = self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['context'] = context
        return data['form']


    def _check_state(self, cr, uid, data, context):
        if data['form']['state'] == 'bydate':
            self._check_date(cr, uid, data, context)
        return data['form']


    def _check_date(self, cr, uid, data, context):
        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' between f.date_start and f.date_stop """%(data['form']['date_from'])
        cr.execute(sql)
        res = cr.dictfetchall()
        if res:
            if (data['form']['date_to'] > res[0]['date_stop'] or data['form']['date_to'] < res[0]['date_start']):
                raise  wizard.except_wizard(_('UserError'),_('Date to must be set between %s and %s') % (res[0]['date_start'], res[0]['date_stop']))
            else:
                return 'report'
        else:
            raise wizard.except_wizard(_('UserError'),_('Date not in a defined fiscal year'))

    def _excel_create(self, cr, uid, data, context={}):
        form = data['form']

        account_ids = form['account_list'][0][2]
        fiscal_year_label = utils.get_fiscalyear_text(cr, uid, form)
        periods_label = utils.get_periods_and_date_text(cr, uid, form)

        csv_file = '\n'
        csv_file += 'Fiscal year: {}\n'.format(fiscal_year_label)

        if len(periods_label) != 0:
            csv_file += 'Periods/Date range: {}\n'.format(periods_label)

        csv_file += '\n'
        csv_file += ';;Period;Period;Period;Period;F. Year;F. Year;F. Year;F. Year\n'
        csv_file += 'Code;Account;Init. Balance;Debit;Credit;Balance;Init. Balance;Debit;Credit;Balance\n\n'

        lines = utils.lines(self, cr, uid, form, ids=account_ids, done=None, level=0, context=context)

        for line in lines:
            csv_file += '{};{};'.format(line['code'], line['name'])

            period_init = utils.float_string(line['balanceinit'])
            period_debit = utils.float_string(line['debit'])
            period_credit = utils.float_string(line['credit'])
            period_balance = utils.float_string(line['balance'])
            csv_file += '{};{};{};{};'.format(period_init, period_debit, period_credit, period_balance)

            fy_init = utils.float_string(line['balanceinit_fy'])
            fy_debit = utils.float_string(line['debit_fy'])
            fy_credit = utils.float_string(line['credit_fy'])
            fy_balance = utils.float_string(line['balance_fy'])
            csv_file += '{};{};{};{}\n'.format(fy_init,fy_debit, fy_credit, fy_balance)

        data['form']['file'] = base64.b64encode(csv_file)
        data['form']['name'] = 'Account balance.csv'

        return data['form']

    def _report_async(self, cr, uid, datas, context={}):
        datas = {
            'form': {
                'date_from': '2021-01-01',
                'display_account_level': 0,
                'company_id': 1,
                'state': 'none',
                'account_list': [[6, 0, [8, 9, 1, 2, 3, 7, 4, 5, 6]]],
                'periods': [[6, 0, []]],
                'context': {'lang': False, 'tz': False},
                'date_to': '2021-12-16',
                'display_account': 'bal_all',
                'fiscalyear': 1
            }, 
            
            'ids': [285],
            'report_type': 'pdf',
            'model': 'ir.ui.menu',
            'id': 285
        }

        AsyncReports = self.pool.get('async.reports').browse(cr, uid, uid, context=context)
        report_id = AsyncReports.async_report_report(cr, uid, [], 'account.balance.full', {}, context)
        return datas['form']

    def check_all_accounts(self, cr, uid, data, context={}):
        if data['form']['all_accounts']:
            all_accounts = self.pool.get('account.account').search(cr, uid, [])
            data['form']['account_list'][0] = [6, 0, all_accounts]
        elif data['form']['account_list'][0] == [6,0, []]:
            raise wizard.except_wizard(_("Error"), _("Account list or 'all accounts' check required"))
        return data['form']


    """
    states = {

        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch': options_form, 'fields': options_fields, 'state':[('end','Cancel','gtk-cancel'),('report','Print','gtk-print'),
                ('report_async', 'Send by email', 'gtk-home'), ('excelFile', 'Excel', 'gtk-save')]}
        },
        'excelFile': {
            'actions':[_excel_create, check_all_accounts],
            'result': {'type':'form', 'arch':excel_form, 'fields':excel_fields, 'state':[('end', 'Sortir', 'gtk-close')]}
        },
        'report': {
            'actions': [_check_state, check_all_accounts],
            'result': {'type':'print', 'report':'account.balance.full', 'state':'end'}
        },
        'report_async': {
            'actions': [_report_async, check_all_accounts],
            'result': {'type':'state', 'state': 'end'}
        }
    }"""

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'account_list': fields.many2many(
            'account.account', 'sw_wiz_account_ref',
            'wiz_account_id', 'account_id', string='Root accounts',
            domain=[]
        ),
        'all_accounts': fields.boolean(u"All accounts", help=u'This check will include all accounts'),
        'state': fields.selection([('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')], _(u'Date/Period Filter')),
        'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscal year', help=u'Keep empty to use all open fiscal years to compute the balance'),
        'periods': fields.many2many(
            'account.period', 'sw_wiz_account_period_ref',
            'wiz_account_period_id', 'account_period_id', string='Periods',
            help=u'All periods in the fiscal year if empty',
        ),
        'display_account': fields.selection([('bal_all','All'),('bal_solde', 'With balance'),('bal_mouvement','With movements')],
            _(u'Display accounts')
        ),
        'display_account_level': fields.integer(_(u"Up to level"), help=u'Display accounts up to this level (0 to show all)'),
        'date_from': fields.date(u"Start date", required=True),
        'date_to': fields.date(u"End date", required=True),
    }
    _defaults = {
        'state': lambda *a:'none',
        'all_accounts': lambda *a: False,
        'display_account_level': lambda *a: 0,
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
    }

WizardAccountBalanceReport()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
