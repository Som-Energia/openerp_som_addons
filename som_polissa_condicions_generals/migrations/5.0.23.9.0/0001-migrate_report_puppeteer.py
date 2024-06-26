# coding=utf-8

import logging

from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Creating pooler")

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    list_of_records = [
        "giscedata_polissa.report_contracte",
        "giscedata_polissa.value_contracte",
    ]
    load_data_records(
        cursor, "som_polissa_condicions_generals",
        "report/giscedata_polissa_condicions_generals_report.xml", list_of_records, mode="update"
    )
    logger.info("giscedata_polissa_condicions_generals_report.xml successfully updated")

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    list_of_records = [
        "report_contracte_m101",
        "value_report_contracte_m101",
    ]
    load_data_records(
        cursor, "som_polissa_condicions_generals_m101",
        "giscedata_polissa_condicions_generals_m101_report.xml", list_of_records, mode="update"
    )
    logger.info("giscedata_polissa_condicions_generals_m101_report.xml successfully updated")

    # Actualitzar tots els permisos
    logger.info("Updating access CSV")
    load_data(
        cursor, 'som_template', 'security/ir.model.access.csv', idref=None, mode='update'
    )
    logger.info("CSV succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
