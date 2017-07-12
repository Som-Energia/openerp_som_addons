# coding=utf-8
from oopgrade import oopgrade
import netsvc
from consolemsg import step, warn, success, error, fail

version = "somenergia-generationkwh_0.0.1.4: "

def migrate(cr,v):
    print version + "Hem entrat al Migrate"  


    query = """\
        select
            inv.id as id
        from
            generationkwh_investment as inv
        left join
            account_move_line as ml
        on
            inv.move_line_id = ml.id
        left join
            account_period as p
        on
            p.id = ml.period_id
        where
            p.special and
            inv.active
       """
    cr.execute(query)
    result = cr. fetchone()
    
    if result:
        fail("Error: Hi ha inversions a Generationkwh de tancament actives!")
    else:
        query = """\
            delete
            from generationkwh_investment
            where id in (
                select
                    inv.id as id
                from
                    generationkwh_investment as inv
                left join
                    account_move_line as ml
                on
                    inv.move_line_id = ml.id
                left join
                    account_period as p
                on
                    p.id = ml.period_id
                where
                    p.special and
                    not inv.active
                )
            """

        cr.execute(query)
        print "S'han eliminat %d inversions creades pel tancament." % cr.rowcount

 
#    fail("Oriol: Aquesta és una errada de prova a veure que fa amb la versió")
    return

def up(cursor, installed_version):
    print version + "Hem entrat al UP"
    pass

def down(cursor):
    print version + "Hem entrat al Down"
    pass

# vim: ts=4 sw=4 et
