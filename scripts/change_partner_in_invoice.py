import configdb
from erppeek import Client as Client
import psycopg2

print "Connectant"
c = Client(**configdb.erppeek)
print "Connectat"

write_vals = False
fact_number = 'FE2200231739'
partner_id = 204530
mandate_id = 315028

partner_obj = c.model('res.partner')
partner_new = partner_obj.browse(partner_id)

address_new = partner_new.address
bank_new = partner_new.bank_ids

mandate_obj = c.model('payment.mandate')
mandate_new = mandate_obj.browse(mandate_id)

fact_obj = c.model('giscedata.facturacio.factura')
fact_id = fact_obj.search([('number','=',fact_number)])
fact = fact_obj.browse(fact_id[0])
old_partner_id = fact.partner_id.id


def change_account_invoice(invoice, vals, to_write_vals):

    address = vals['address']
    bank = vals['bank']
    partner = vals['partner']
    mandate = vals['mandate']

    ## invoice_id (account.invoice)

    ai_obj = c.model('account.invoice')
    ai = ai_obj.browse(invoice.id)

    ai_old_vals = {
        'address_contact_id': ai.address_contact_id.id,
        'address_invoice_id': ai.address_invoice_id.id,
        'partner_bank': ai.partner_bank.id,
        'partner_id': ai.partner_id.id,
        'mandate_id': ai.mandate_id.id if ai.mandate_id else None
    }

    ai_vals = {
        'address_contact_id': address,
        'address_invoice_id': address,
        'partner_bank': bank,
        'partner_id': partner,
        'mandate_id': mandate
    }

    if ai_old_vals == ai_vals:
        print "Warning: Account Invoice {} already changed, nothing to do.".format(ai.number)
        return True

    print 'ai_old_vals ', ai_old_vals
    print 'ai_vals ', ai_vals

    if to_write_vals:
        ai_obj.write(ai.id, ai_vals)

        print 'Ai changed values: '
        print 'address_contact_id ', ai.address_contact_id.id
        print 'address_invoice_id ', ai.address_invoice_id.id
        print 'partner_bank ', ai.partner_bank.id
        print 'partner_id ', ai.partner_id
        print 'mandate_id ', ai.mandate_id
    else:
        print 'NOT to write values'



if partner_new and fact:
    print 'Parter and fact exists ', partner_new.name, fact.number

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


# Consider move to somutils.dbutils
def run_query(dbconn, query, kwds={}):
    from yamlns import namespace as ns
    def fetchNs(cursor):
	"""
		Wraps a database cursor so that instead of providing data
		as arrays, it provides objects with attributes named
		as the query column names.
	"""

	fields = [column.name for column in cursor.description]
	for row in cursor:
		yield ns(zip(fields, row))

    def nsList(cursor):
        return [e for e in fetchNs(cursor) ]

    with dbconn.cursor() as cursor :
        try:
            cursor.execute(query, kwds)
        except KeyError as e:
            key = e.args[0]
            raise Exception(key)
        if cursor.description:
            return nsList(cursor)
        else:
            print cursor.statusmessage
            dbconn.commit()


try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database " + configdb.psycopg['database']
    raise ex

#dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

if partner_new and fact: # and write_vals:

    # ACCOUNT MOVE LINE
    result = run_query(dbconn, """select m.id, l.move_id, l.id, l.partner_id
            from account_move m inner join account_move_line l on l.move_id = m.id
            where m.ref = %(number)s and l.partner_id = %(old_partner)s""", {'number': fact_number, 'old_partner': old_partner_id})
    print "{} account_move_line to modify".format(len(result))
    if result and write_vals:
        run_query(dbconn, """update account_move_line
            set partner_id = %(new_partner)s
            from (
                select l.id as line_id
                from account_move m inner join account_move_line l on l.move_id = m.id
                where m.ref = %(number)s and l.partner_id = %(old_partner)s
            ) as subquery   where id = subquery.line_id""", {'number': fact_number, 'old_partner': old_partner_id, 'new_partner': partner_id})

    # PAYMENT LINE
    result = run_query(dbconn, """select p.id as p_id
            from payment_line p
            inner join account_move_line l on l.id = p.move_line_id
            inner join account_move m on m.id = l.move_id
            where m.ref = %(number)s and p.partner_id = %(old_partner)s""", {'number': fact_number, 'old_partner': old_partner_id})
    print "{} payment_line to modify".format(len(result))
    if result: # and write_vals:
        run_query(dbconn,"""update payment_line
            set partner_id = %(new_partner)s
            from (
                select p.id as p_id
                from payment_line p
                inner join account_move_line l on l.id = p.move_line_id
                inner join account_move m on m.id = l.move_id
                where m.ref = %(number)s and p.partner_id = %(old_partner)s
            ) as subquery
            where id = subquery.p_id
            """, {'number': fact_number, 'old_partner': old_partner_id, 'new_partner': partner_id})
