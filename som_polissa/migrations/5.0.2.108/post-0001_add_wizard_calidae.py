# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data, add_columns


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    # AFEGIR UNA COLUMNA AL MODEL
    logger.info("Adding column importacio_cadastre_incidencies_origen to giscedata_cups_ps")
    add_columns(
        cursor, {
            'giscedata_cups_ps': [
                ('importacio_cadastre_incidencies_origen', 'character varying(128)')
            ]
        }
    )
    logger.info("Column added succesfully.")

    # UPATAR UN XML SENCER##
    logger.info("Updating XMLs")
    xmls = [
        "giscedata_cups_view.xml",
        "wizard/wizard_import_ref_cadastral_from_csv_view.xml",
        "security/ir.model.access.csv",
    ]
    for xml_w in xmls:
        load_data(
            cursor, 'som_polissa', xml_w, idref=None, mode='update'
        )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
