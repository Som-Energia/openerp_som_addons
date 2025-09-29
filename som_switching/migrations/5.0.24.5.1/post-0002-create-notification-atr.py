# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)

    # UPDATAR UN XML SENCER#
    logger.info("Updating XML from giscedata_switching/giscedata_switching_notification_data.xml")
    list_of_records = [
        "sw_not_m1_altres_02",
        "sw_not_b107",
        "sw_not_b102",
    ]
    load_data_records(
        cursor, 'giscedata_switching', 'giscedata_switching_notification_data.xml',
        list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating XML giscedata_switching_notification_data.xml")
    load_data(
        cursor,
        "som_switching",
        "giscedata_switching_notification_data.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    gsnc_obj = pool.get('giscedata.switching.notificacio.config')
    imd_obj = pool.get('ir.model.data')
    uid = 1
    logger.info("Actualitzar estat notificacions")
    # Activar B1 02 rebuig i 07 motiu 01
    llista_ids_activar = []
    llista_ids_activar.append(imd_obj.get_object_reference(
        cursor, uid, 'som_switching',
        'sw_not_b102_rebuig'
    )[1])
    llista_ids_activar.append(imd_obj.get_object_reference(
        cursor, uid, 'som_switching',
        'sw_not_b107_motiu_01'
    )[1])
    gsnc_obj.write(
        cursor, uid, llista_ids_activar, {'active': True}
    )

    # Desactivar B1 02
    llista_ids_desactivar = []
    llista_ids_desactivar.append(imd_obj.get_object_reference(
        cursor, uid, 'som_switching',
        'sw_not_b102_motiu_01'
    )[1])
    llista_ids_desactivar.append(imd_obj.get_object_reference(
        cursor, uid, 'som_switching',
        'sw_not_m1_altres_02_acceptacio'
    )[1])
    gsnc_obj.write(
        cursor, uid, llista_ids_desactivar, {'active': False}
    )


def down(cursor, installed_version):
    pass


migrate = up
