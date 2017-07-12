# coding=utf-8
from oopgrade import oopgrade
import netsvc


def migrate(cr,v):
    print "somenergia-generationkwh_0.0.1.1: Hem entrat al Migrate"
    return

def up(cursor, installed_version):
    logger= netsvc.Logger()
    print "somenergia-generationkwh_0.0.1.1: Hem entrat al UP"
    if not installed_version:
        return

    logger.notifyChannel('migration', netsvc.LOG_INFO, 'Changing ir_model_data from giscedata_facturacio_comer to giscedata_facturacio')
    '''cursor.execute("delete
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
                not inv.active")'''

    logger.notifyChannel('migration', netsvc.LOG_INFO, 'Succesfully changed')


def down(cursor):
    print "somenergia-generationkwh_0.0.1.1: Hem entrat al Down"
    pass

# vim: ts=4 sw=4 et
