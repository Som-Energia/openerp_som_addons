# -*- coding: utf-8 -*-
from erppeek import Client
from datetime import timedelta,datetime
import tqdm

now=datetime.now()
print "========================"
print now

def last_month_invoices(now,limit=None):
    end_date=datetime(now.year,now.month,1)-timedelta(days=1)
    start_date=datetime(end_date.year,end_date.month,1)
    ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    return ids[:limit]


def current_month_invoices(now,limit=None):
    end_date=datetime(now.year,now.month,now.day)
    start_date=datetime(end_date.year,end_date.month,1)
    ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    return ids[:limit]


#Canviat el 18/06/2019
def before_3days_invoices(now, limit=None):
    end_date=datetime(now.year,now.month,now.day)-timedelta(days=3)
    # start_date=datetime(end_date.year,end_date.month,end_date.day)-timedelta(days=120) Canviat el 25/07/2022
    start_date=datetime(end_date.year,end_date.month,end_date.day)-timedelta(days=240)
    ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    #Afegit el dia 25/07/2022
    ids_ab = O.GiscedataFacturacioFactura.search([('type','=','in_refund'), ('tipo_rectificadora','!=','BRA'),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    ids += ids_ab
    return ids[:limit]


def open_invoices():
    O = Client(**dbconfig.erppeek)
    ids = before_3days_invoices(datetime.now(),limit=10000)
    n_invoices = 0
    invoice_err = []
    for id_ in tqdm.tqdm(ids):
        try:
           ctx = {'active_ids': [id_]}
           wiz_o = O.GiscedataFacturacioSwitchingAprovarFactura
           wizard_id = wiz_o.create({'open_1ct_diff_invoices': True, 'open_negative_invoices': False}, ctx)
           wiz_o.action_aprovar_factures([wizard_id],ctx)
           n_invoices = n_invoices + 1
        except Exception, e:
           print e
           invoice_err.append(id_)
           pass

    print "S'han obert un total de " + str(n_invoices) + " factures."
    print "Factures que no s'han pogut obrir:"
    print invoice_err


if __name__=='__main__':
    open_invoices()
