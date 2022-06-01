# -*- coding: utf-8 -*-
#from ooop import OOOP
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

#Canviat el 25/10/2017
def before_15days_invoices(now, limit=None):
    end_date=datetime(now.year,now.month,now.day)-timedelta(days=15)
    start_date=datetime(end_date.year,end_date.month,end_date.day)-timedelta(days=120)
    ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    return ids[:limit]

#Canviat el 11/01/2018
def before_7days_invoices(now, limit=None):
    end_date=datetime(now.year,now.month,now.day)-timedelta(days=7)
    start_date=datetime(end_date.year,end_date.month,end_date.day)-timedelta(days=120)
    ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    return ids[:limit]

#Canviat el 18/06/2019
def before_3days_invoices(now, limit=None):
    end_date=datetime(now.year,now.month,now.day)-timedelta(days=3)
    start_date=datetime(end_date.year,end_date.month,end_date.day)-timedelta(days=120)
    ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
                                               ('state','=','draft'),
                                               ('date_invoice','>=',start_date.strftime("%Y-%m-%d")),
                                               ('date_invoice','<=',end_date.strftime("%Y-%m-%d"))])
    return ids[:limit]

### PRUEBA DICIEMBRE AÑO ANTERIOR
##print "PRUEBA DICIEMBRE AÑO ANTERIOR"
##now = datetime(2016,1,1)
##ids = last_month_invoices(datetime(2016,1,12))
##print len(ids)
##ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
##                                           ('state','=','draft'),
##                                           ('date_invoice','>=','2015-12-01'),
##                                           ('date_invoice','<=','2015-12-31')])
##print len(ids)
##
### PRUEBA FEBRERO AÑO 2015
##print "PRUEBA FEBRERO AÑO 2015"
##now = datetime(2015,3,2)
##ids = last_month_invoices(now)
##print len(ids)
##ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
##                                           ('state','=','draft'),
##                                           ('date_invoice','>=','2015-02-01'),
##                                           ('date_invoice','<=','2015-02-28')])
##print len(ids)
##
##
### PRUEBA JUNIO AÑO 2015
##print "PRUEBA JUNIO AÑO 2015"
##now = datetime(2015,7,12)
##ids = last_month_invoices(datetime(2015,7,12))
##print len(ids)
##ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
##                                           ('state','=','draft'),
##                                           ('date_invoice','>=','2015-06-01'),
##                                           ('date_invoice','<=','2015-06-30')])
##print len(ids)
##
### PRUEBA ENERO ESTE AÑO
##print "PRUEBA ENERO ESTE AÑO"
##now = datetime.now()
##ids = last_month_invoices(now,limit=30)
##print len(ids)
##ids = O.GiscedataFacturacioFactura.search([('type','in',['in_invoice']),
##                                           ('state','=','draft'),
##                                           ('date_invoice','>=','2016-01-01'),
##                                           ('date_invoice','<=','2016-01-31')])
##print len(ids)



def open_invoices():
    #ids = last_month_invoices(datetime.now(),limit=10000)
    #ids = last_month_invoices(datetime.now(),limit=20000)
    #ids = before_15days_invoices(datetime.now(),limit=10000)
    O = Client(**dbconfig.erppeek)
    ids = before_3days_invoices(datetime.now(),limit=10000)
    n_invoices = 0
    invoice_err = []
    for id_ in tqdm.tqdm(ids):
        print id_
        try:
           ctx = {'active_ids': [id_]}
           wizard_id = O.GiscedataFacturacioSwitchingAprovarFactura.create({}, ctx)
           wizard = O.GiscedataFacturacioSwitchingAprovarFactura.get(wizard_id)
           # Canviat el 01/06/2022 perquè Endesa ens envia factures equivocades
           # en negatiu i després en positiu
           #wizard.write({'open_1ct_diff_invoices': True, 'open_negative_invoices': True})
           wizard.write({'open_1ct_diff_invoices': True})
           #wizard.action_aprovar_factures(ctx)
           n_invoices = n_invoices + 1
        except Exception, e:
           invoice_err.append(id_)
           pass

    print "S'han obert un total de " + str(n_invoices) + " factures."
    print "Factures que no s'han pogut obrir:"
    print invoice_err


if __name__=='__main__':
    open_invoices()
