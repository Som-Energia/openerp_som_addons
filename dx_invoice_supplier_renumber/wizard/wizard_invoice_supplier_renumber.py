# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import wizard
import pooler

_invoice_supplier_renumber_form = """<?xml version="1.0"?>
            <form string="Report Options">
                <field name="company_id"/>
                <newline/>
                <separator string="Time Filter" colspan="4"/>
                <group colspan="4" col="6">
                    <field name="time_filter_by"/>
                    <group colspan="4" col="4">
                        <group colspan="2" col="2"  attrs="{'invisible':[('time_filter_by','!=','period')]}">
                            <field name="period_id" />
                        </group>
                        <group colspan="2" col="2"  attrs="{'invisible':[('time_filter_by','!=','fiscalyear')]}">
                            <field name="fiscalyear_id" />
                        </group>
                        <group colspan="4" col="4"  attrs="{'invisible':[('time_filter_by','!=','dates')]}">
                            <field name="date_from"/>
                            <field name="date_to"/>
                        </group>
                    </group>
                </group>
                <separator string="Init" colspan="4"/>
                <group colspan="4" col="4">
                    <field name="init" colspan="4" nolabel="1"/>
                </group>
            </form>"""  # noqa: E501

_invoice_supplier_renumber_fields = {
    "company_id": {"string": "Company", "type": "many2one", "relation": "res.company"},
    "period_id": {"string": "Period", "type": "many2one", "relation": "account.period"},
    "fiscalyear_id": {
        "string": "Fiscal year",
        "type": "many2one",
        "relation": "account.fiscalyear",
        "help": "Keep empty for all open fiscal year",
    },
    "date_from": {
        "string": "Date from",
        "type": "date",
    },
    "date_to": {
        "string": "Date To",
        "type": "date",
    },
    "init": {
        "string": "Init Number",
        "type": "integer",
        "relation": "account.fiscalyear",
        "default": lambda *a: 1,
    },
    "time_filter_by": {
        "string": "Time Filter by",
        "type": "selection",
        "selection": [
            ("fiscalyear", "Fiscal Year"),
            ("period", "Period"),
            ("dates", "Dates"),
            ("none", "None"),
        ],
        "required": True,
        "default": lambda *a: "none",
    },
}


def _get_defaults(self, cr, uid, data, context):

    fiscalyear_obj = pooler.get_pool(cr.dbname).get("account.fiscalyear")
    data["form"]["fiscalyear_id"] = fiscalyear_obj.find(cr, uid)
    data["form"]["company_id"] = (
        pooler.get_pool(cr.dbname).get("res.users").browse(cr, uid, uid).company_id.id
    )
    return data["form"]


def _renumber(self, cr, uid, data, context):
    invoice_obj = pooler.get_pool(cr.dbname).get("account.invoice")
    period_obj = pooler.get_pool(cr.dbname).get("account.period")
    fiscalyear_obj = pooler.get_pool(cr.dbname).get("account.fiscalyear")

    date_start = False
    date_stop = False
    if data["form"]["time_filter_by"] == "dates":
        date_start = data["form"]["date_from"]
        date_stop = data["form"]["date_to"]
    elif data["form"]["time_filter_by"] == "period":
        period = period_obj.browse(cr, uid, [data["form"]["period_id"]], context=context)[0]
        date_start = period.date_start
        date_stop = period.date_stop
    elif data["form"]["time_filter_by"] == "fiscalyear":
        fiscalyear = fiscalyear_obj.browse(
            cr, uid, [data["form"]["fiscalyear_id"]], context=context
        )[0]
        date_start = fiscalyear.date_start
        date_stop = fiscalyear.date_stop

    filter = [("state", "in", ("open", "paid")), ("type", "in", ["in_invoice", "in_refund"])]

    if date_start:
        filter.append(("date_invoice", ">=", date_start))

    if date_stop:
        filter.append(("date_invoice", "<=", date_stop))

    invoice_ids = invoice_obj.search(cr, uid, filter, order="date_invoice", context=context)

    invoice_ids = invoice_obj.renumber(cr, uid, invoice_ids, data["form"]["init"], context=context)

    return {}


class wizard_invoice_supplier_renumber(wizard.interface):
    states = {
        "init": {
            "actions": [_get_defaults],
            "result": {
                "type": "form",
                "arch": _invoice_supplier_renumber_form,
                "fields": _invoice_supplier_renumber_fields,
                "state": [("end", "Cancel"), ("renumber", "Renumber")],
            },
        },
        "renumber": {
            "actions": [],
            "result": {"type": "action", "action": _renumber, "state": "end"},
        },
    }


wizard_invoice_supplier_renumber("invoice.supplier.renumber")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
