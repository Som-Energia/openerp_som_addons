# coding=utf-8
import logging
from oopgrade.oopgrade import column_exists, add_columns


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("New field 'mesos_factura_mes_antiga_impagada' in 'giscedata.polissa'")

    if column_exists(cursor, 'giscedata_polissa', 'mesos_factura_mes_antiga_impagada'):
        logger.info('Column mesos_factura_mes_antiga_impagada already exists. Passing')
        return

    logger.info('Adding column mesos_factura_mes_antiga_impagada to giscedata_polissa')
    add_columns(cursor, {
        'giscedata_polissa': [('mesos_factura_mes_antiga_impagada', 'int')]
    })

    logger.info('Updating all giscedata_polissa rows field mesos_factura_mes_antiga_impagada to 0')
    cursor.execute("UPDATE giscedata_polissa SET mesos_factura_mes_antiga_impagada=0")
    logger.info('Updated %s records', cursor.rowcount)


def down(cursor, installed_version):
    pass


migrate = up
