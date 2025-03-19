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
import time
import netsvc
from account_financial_report.utils import account_balance_utils as utils
from datetime import datetime
from tools.translate import _
from osv import osv, fields
from oorq.decorators import job


class WizardAccountBalanceReport(osv.osv_memory):

    _name = "wizard.account.balance.report"

    def _get_defaults(self, cr, uid, ids, datas, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        user = self.pool.get("res.users").browse(cr, uid, uid, context=context)
        if user.company_id:
            company_id = user.company_id.id
        else:
            company_id = self.pool.get("res.company").search(cr, uid, [("parent_id", "=", False)])[
                0
            ]
        fiscalyear_obj = self.pool.get("account.fiscalyear")
        form = {}
        form["company_id"] = company_id
        form["fiscalyear"] = fiscalyear_obj.find(cr, uid)
        datas["form"].update(**form)
        return True

    def _check_state(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        report = self.browse(cr, uid, ids)
        if report.state and report.state == "bydate":
            self._check_date(cr, uid, ids, context)
        return True

    def _check_date(self, cr, uid, data, context=None):
        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' between f.date_start and f.date_stop """ % (
            data["form"]["date_from"]
        )
        cr.execute(sql)
        res = cr.dictfetchall()
        if res:
            if (
                data["form"]["date_to"] > res[0]["date_stop"]
                or data["form"]["date_to"] < res[0]["date_start"]
            ):
                raise osv.except_osv(
                    _("UserError"),
                    _("Date to must be set between %s and %s")
                    % (res[0]["date_start"], res[0]["date_stop"]),
                )
            else:
                return "report"
        else:
            raise osv.except_osv(_("UserError"), _("Date not in a defined fiscal year"))

    def get_account_balance_wiz_data(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]

        wiz = self.browse(cr, uid, ids, context)
        datas = {
            "form": {
                "date_from": wiz.date_from,
                "display_account_level": wiz.display_account_level,
                "company_id": wiz.company_id.id,
                "state": wiz.state,
                "account_list": [(6, 0, [item.id for item in wiz.account_list])],
                "periods": [(6, 0, wiz.periods)],
                "date_to": wiz.date_to,
                "display_account": wiz.display_account,
                "fiscalyear": wiz.fiscalyear.id,
                "context": context,
                "all_accounts": wiz.all_accounts,
            }
        }
        self.check_all_accounts(cr, uid, ids, datas, context)
        return datas

    def _excel_create(self, cr, uid, ids, datas, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        form = datas["form"]
        account_ids = form["account_list"][0][2]
        fiscal_year_label = utils.get_fiscalyear_text(cr, uid, form)
        periods_label = utils.get_periods_and_date_text(cr, uid, form)

        csv_file = "\n"
        csv_file += "Fiscal year: {}\n".format(fiscal_year_label)

        if len(periods_label) != 0:
            csv_file += "Periods/Date range: {}\n".format(periods_label)

        csv_file += "\n"
        csv_file += ";;Period;Period;Period;Period;F. Year;F. Year;F. Year;F. Year\n"
        csv_file += (
            "Code;Account;Init. Balance;Debit;Credit;Balance;Init. Balance;Debit;Credit;Balance\n\n"
        )

        lines = utils.lines(
            self, cr, uid, form, ids=account_ids, done=None, level=0, context=context
        )

        for line in lines:
            csv_file += "{};{};".format(line["code"], line["name"])

            period_init = utils.float_string(line["balanceinit"])
            period_debit = utils.float_string(line["debit"])
            period_credit = utils.float_string(line["credit"])
            period_balance = utils.float_string(line["balance"])
            csv_file += "{};{};{};{};".format(
                period_init, period_debit, period_credit, period_balance
            )

            fy_init = utils.float_string(line["balanceinit_fy"])
            fy_debit = utils.float_string(line["debit_fy"])
            fy_credit = utils.float_string(line["credit_fy"])
            fy_balance = utils.float_string(line["balance_fy"])
            csv_file += "{};{};{};{}\n".format(fy_init, fy_debit, fy_credit, fy_balance)

        datas["form"]["file"] = csv_file
        datas["form"]["name"] = "Account balance.csv"

        return datas["form"]

    def check_all_accounts(self, cr, uid, ids, datas, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        if datas["form"]["all_accounts"]:
            all_accounts = self.pool.get("account.account").search(cr, uid, [])
            datas["form"]["account_list"][0] = [6, 0, all_accounts]
        elif datas["form"]["account_list"][0] == [6, 0, []]:
            raise osv.except_osv(_("Error"), _("Account list or 'all accounts' check required"))

    def report_csv_print(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        wizard = self.browse(cr, uid, ids, context)
        datas = self.get_account_balance_wiz_data(cr, uid, ids, context)
        self._get_defaults(cr, uid, ids, datas, context)
        self.check_all_accounts(cr, uid, ids, datas, context)
        result = self._excel_create(cr, uid, ids, datas, context)

        wizard.write(
            {
                "wiz_state": "done",
                "filename_report": "account_balance.csv",
                "report": base64.b64encode(result["file"]),
            }
        )

    @job(queue="waiting_reports")
    def report_csv_send_async(self, cr, uid, ids, datas, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        self._get_defaults(cr, uid, ids, datas, context)
        self.check_all_accounts(cr, uid, ids, datas, context)
        result = self._excel_create(cr, uid, ids, datas, context)

        # TODO: Save file to MongoDB to support workers in different server of main instance
        timestamp = datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        filename = "/tmp/account_balance_" + timestamp
        file = open(filename, "wr")
        file.write(result["file"])
        file.close()

        async_obj = self.pool.get("async.reports")
        mail_data = async_obj.get_datas_email_params(cr, uid, datas, context)
        async_obj.send_mail(
            cr, uid, mail_data["from"], filename, mail_data["email_to"], "account_balance.csv"
        )

    def report_csv_send(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        wizard = self.browse(cr, uid, ids, context)
        user_obj = self.pool.get("res.users")
        user = user_obj.browse(cr, uid, uid, context)
        info = ""
        if user.address_id and user.address_id.email:
            info = "S'enviarà el resultat al correu associat a l'usuaria {}: ({})".format(
                user.login, user.address_id.email
            )
        wizard.write({"wiz_state": "send", "info": info})
        datas = self.get_account_balance_wiz_data(cr, uid, ids, context)
        self.report_csv_send_async(cr, uid, ids, datas, context)

    def report_pdf_print(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        wizard = self.browse(cr, uid, ids, context)
        datas = self.get_account_balance_wiz_data(cr, uid, ids, context)
        self._get_defaults(cr, uid, ids, datas, context)
        self.check_all_accounts(cr, uid, ids, datas, context)
        self._check_state(cr, uid, ids, context)
        report_name = "report.account.balance.full"
        obj = netsvc.LocalService(report_name)
        result, format = obj.create(cr, uid, ids, datas, context)

        wizard.write(
            {
                "wiz_state": "done",
                "filename_report": "account_balance.pdf",
                "report": base64.b64encode(result),
            }
        )

    @job(queue="waiting_reports")
    def report_pdf_send_async(self, cr, uid, ids, datas, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        self._get_defaults(cr, uid, ids, datas, context)
        self.check_all_accounts(cr, uid, ids, datas, context)
        async_obj = self.pool.get("async.reports")
        async_obj.async_report_report(cr, uid, ids, "account.balance.full", datas, context)

    def report_pdf_send(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if isinstance(ids, list):
            ids = ids[0]
        wizard = self.browse(cr, uid, ids, context)
        user_obj = self.pool.get("res.users")
        user = user_obj.browse(cr, uid, uid, context)
        info = ""
        if user.address_id and user.address_id.email:
            info = "S'enviarà el resultat al correu associat a l'usuaria {}: ({})".format(
                user.login, user.address_id.email
            )
        wizard.write({"wiz_state": "send", "info": info})
        datas = self.get_account_balance_wiz_data(cr, uid, ids, context)
        self.report_pdf_send_async(cr, uid, ids, datas, context)

    _columns = {
        "company_id": fields.many2one("res.company", "Company", required=True),
        "account_list": fields.many2many(
            "account.account",
            "sw_wiz_account_ref",
            "wiz_account_id",
            "account_id",
            string="Root accounts",
            domain=[],
        ),
        "all_accounts": fields.boolean(
            u"All accounts", help=u"This check will include all accounts"
        ),
        "state": fields.selection(
            [
                ("bydate", "By Date"),
                ("byperiod", "By Period"),
                ("all", "By Date and Period"),
                ("none", "No Filter"),
            ],
            _(u"Date/Period Filter"),
        ),
        "fiscalyear": fields.many2one(
            "account.fiscalyear",
            "Fiscal year",
            help=u"Keep empty to use all open fiscal years to compute the balance",
        ),
        "periods": fields.many2many(
            "account.period",
            "sw_wiz_account_period_ref",
            "wiz_account_period_id",
            "account_period_id",
            string="Periods",
            help=u"All periods in the fiscal year if empty",
        ),
        "display_account": fields.selection(
            [
                ("bal_all", "All"),
                ("bal_solde", "With balance"),
                ("bal_mouvement", "With movements"),
            ],
            _(u"Display accounts"),
        ),
        "display_account_level": fields.integer(
            _(u"Up to level"), help=u"Display accounts up to this level (0 to show all)"
        ),
        "date_from": fields.date(u"Start date", required=True),
        "date_to": fields.date(u"End date", required=True),
        "filename_report": fields.char("Nom fitxer exportat", size=256),
        "report": fields.binary("Report Result"),
        "info": fields.text("Description"),
        "wiz_state": fields.selection([("done", "Done"), ("send", "Send")], "wizard state"),
    }

    _defaults = {
        "wiz_state": lambda *a: "filter",
        "state": lambda *a: "none",
        "all_accounts": lambda *a: False,
        "display_account_level": lambda *a: 0,
        "date_from": lambda *a: time.strftime("%Y-01-01"),
        "date_to": lambda *a: time.strftime("%Y-%m-%d"),
    }


WizardAccountBalanceReport()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
