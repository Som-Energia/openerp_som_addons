# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals
from erppeek import Client
from datetime import timedelta, datetime
import dbconfig


# Canviat el 18/06/2019
def before_3days_invoices(conn, now, limit=None):
    end_date = datetime(now.year, now.month, now.day) - timedelta(days=3)
    # Canviat el 25/07/2022
    # start_date=datetime(end_date.year,end_date.month,end_date.day)-timedelta(days=120)
    start_date = datetime(end_date.year, end_date.month, end_date.day) - timedelta(days=240)
    ids = conn.GiscedataFacturacioFactura.search(
        [('type', 'in', ['in_invoice']),
         ('state', '=', 'draft'),
         ('date_invoice', '>=', start_date.strftime("%Y-%m-%d")),
         ('date_invoice', '<=', end_date.strftime("%Y-%m-%d"))])
    # Afegit el dia 25/07/2022
    ids_ab = conn.GiscedataFacturacioFactura.search(
        [('type', '=', 'in_refund'), ('tipo_rectificadora', '!=', 'BRA'),
         ('state', '=', 'draft'),
         ('date_invoice', '>=', start_date.strftime("%Y-%m-%d")),
         ('date_invoice', '<=', end_date.strftime("%Y-%m-%d"))])
    ids += ids_ab
    return ids[:limit]


def open_invoices():
    now = datetime.now()
    print("========================")
    print(now)
    conn = Client(**dbconfig.erppeek)
    ids = before_3days_invoices(conn, datetime.now(), limit=10000)
    n_invoices = 0
    invoice_err = []
    for id_ in ids:
        try:
            ctx = {'active_ids': [id_]}
            wiz_o = conn.GiscedataFacturacioSwitchingAprovarFactura
            wizard_id = wiz_o.create({'open_1ct_diff_invoices': True,
                                     'open_negative_invoices': False}, ctx)
            wiz_o.action_aprovar_factures([wizard_id], ctx)
            n_invoices = n_invoices + 1
        except Exception as e:
            print(e)
            invoice_err.append(id_)

    print("S'han obert un total de {0} factures.".format(str(n_invoices)))
    print("Factures que no s'han pogut obrir: {0}".format(invoice_err))
    now = datetime.now()
    print("========================")
    print(now)


if __name__ == '__main__':
    open_invoices()
