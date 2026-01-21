# coding=utf-8
import netsvc
from consolemsg import step, warn, success, error, fail
import logging

version = "somenergia-generationkwh_1.6: "

def migrate(cr,v):
    if not v:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Check if exist an investment created in special period that remains active")
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
        raise Exception("Error: Fix active investments in Generationkwh created in special period")
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
        logger.info("Deleted %d investments created in special period" % cr.rowcount)

    return

def up(cursor, installed_version):
    pass

def down(cursor):
    pass

# vim: ts=4 sw=4 et
