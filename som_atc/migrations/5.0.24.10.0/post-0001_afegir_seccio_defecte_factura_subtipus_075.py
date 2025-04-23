# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Updating XMLs")
    uid = 1
    pool = pooler.get_pool(cursor.dbname)
    gsr_obj = pool.get("giscedata.subtipus.reclamacio")
    imd_obj = pool.get("ir.model.data")
    gsr_xml_id = "subtipus_reclamacio_075"
    gsr_id = imd_obj.get_object_reference(
        cursor, uid, "giscedata_subtipus_reclamacio", gsr_xml_id
    )[1]
    ccs_xml_id = "atc_section_factura"
    ccs_id = imd_obj.get_object_reference(
        cursor, uid, "som_switching", ccs_xml_id
    )[1]

    gsr_obj.write(cursor, uid, gsr_id, {"section_id": [(4, ccs_id)]})

    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
