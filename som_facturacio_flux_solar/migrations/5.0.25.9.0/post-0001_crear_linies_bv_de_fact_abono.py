# -*- coding: utf-8 -*-
import logging
import pooler
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)
    fact_obj = pool.get("giscedata.facturacio.factura")
    uid = 1

    n_factures_procesades, factures_no_processades = fact_obj.crear_descomptes_bv_factures_anulladores(cursor, uid)

    if factures_no_processades:
        msg_process = "Proces finalizat amb avisos"
    else:
        msg_process = "Proces finalizat"
    n_factures_no_processades = len(factures_no_processades)
    n_total_factures = n_factures_procesades + n_factures_no_processades
    logger.info("{}. S'ha processat {} factures anulladores"
                " de {}.".format(msg_process, n_factures_procesades, n_total_factures))
    if n_factures_no_processades:
        logger.info("Per {} factures anulladores no s'ha pogut crear les linies de descompte de bateteria virtual,"
                    " els ids son: {}".format(n_factures_no_processades, factures_no_processades))


def down(cursor, installed_version):
    pass


migrate = up
