import configdb
from erppeek import Client as Client


print "Connectant"
c = Client(**configdb.erppeek)
print "Connectat"

write_vals = False
fact_number = 'FE2200231739'
partner_id = 204530
mandate_id = 241229

partner_obj = c.model('res.partner')
partner_new = partner_obj.browse(partner_id)

address_new = partner_new.address
bank_new = partner_new.bank_ids

mandate_obj = c.model('payment.mandate')
mandate_new = mandate_obj.browse(mandate_id)

fact_obj = c.model('giscedata.facturacio.factura')
fact_id = fact_obj.search([('number','=',fact_number)])
fact = fact_obj.browse(fact_id[0])

   
def change_account_invoice(invoice, vals, to_write_vals):
    
    address = vals['address']
    bank = vals['bank']
    partner = vals['partner']
    mandate = vals['mandate']

    ## invoice_id (account.invoice)

    ai_obj = c.model('account.invoice')
    ai = ai_obj.browse(invoice.id)

    ai_vals = {
        'address_contact_id': address,
        'address_invoice_id': address,
        'partner_bank': bank,
        'partner_id': partner,
        'mandate_id': mandate
            }

    print 'ai_vals ', ai_vals
    
    if to_write_vals:
        ai_obj.write(ai.id, ai_vals) 

        print 'Ai changed values: '
        print 'address_contact_id ', ai.address_contact_id
        print 'address_invoice_id ', ai.address_invoice_id
        print 'partner_bank ', ai.partner_bank
        print 'partner_id ', ai.partner_id
        print 'mandate_id ', ai.mandate_id
    else:
        print 'NOT to write values'
  

if partner_new and fact:
    print 'Parter and fact exists ', partner_new.name, fact.number

    ## Main invoice

    print 'Old values: '
    print 'address_contact_id ', fact.address_contact_id
    print 'address_invoice_id ', fact.address_invoice_id
    print 'partner_bank ', fact.partner_bank
    print 'partner_id ', fact.partner_id

    fact_vals = {
        'address_contact_id': address_new[0].id,
        'address_invoice_id': address_new[0].id,
        'partner_bank': bank_new[0].id,
        'partner_id': partner_new.id,
        'mandate_id': mandate_new.id
    }

    print 'fact_vals ', fact_vals

    if write_vals:
        fact_obj.write(fact.id,fact_vals) 

        print 'Fact changed values: '
        print 'address_contact_id ', fact.address_contact_id
        print 'address_invoice_id ', fact.address_invoice_id
        print 'partner_bank ', fact.partner_bank
        print 'partner_id ', fact.partner_id
        print 'mandate_id ', fact.mandate_id
    else:
        print 'NOT to write values'
        
    vals = {
        'address': address_new[0].id,
        'bank': bank_new[0].id,
        'partner': partner_new.id,
        'mandate': mandate_new.id
    }
    
    ## invoice_id (account.invoice)
    change_account_invoice(fact.invoice_id, vals, write_vals)
    
else:
    print 'Partner or fact does not exists'


"""
#SQL for payments
select m.id, l.move_id, l.id, l.partner_id from account_move m inner join account_move_line l on l.move_id = m.id where m.ref = 'FE2200231739';

begin;
update account_move_line
set partner_id = 204530
from (
	select l.id as line_id from account_move m inner join account_move_line l on l.move_id = m.id where m.ref = 'FE2200231739'
) as subquery
where id = subquery.line_id


select p.id as p_id
from payment_line p
inner join account_move_line l on l.id = p.move_line_id
inner join account_move m on m.id = l.move_id
where m.ref = 'FE2200231739'

begin;
update payment_line 
set partner_id = 204530
from (
select p.id as p_id
from payment_line p
inner join account_move_line l on l.id = p.move_line_id
inner join account_move m on m.id = l.move_id
where m.ref = 'FE2200231739'
) as subquery
where id = subquery.p_id
"""