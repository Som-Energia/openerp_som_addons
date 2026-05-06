# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records, load_access_rules_from_model_name


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    #  Actualitzar un no mòdul al crear-lo i afegir una columna
    logger.info("Creating table: som.template")
    pool.get("som.template")._auto_init(
        cursor, context={'module': 'som_template'}
    )
    logger.info("Table created succesfully.")

    #  Actualitzar un XML/CSV sencer
    logger.info("Updating access CSV")
    load_data(
        cursor, 'som_template', 'security/ir.model.access.csv', idref=None, mode='update'
    )
    logger.info("CSV succesfully updated.")

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    list_of_records = [
        "view_wizard_retipificar_atc_form",
    ]
    load_data_records(
        cursor, 'giscedata_atc', 'wizard/wizard_retipificar_atc.xml', list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")

    # Actualitzar persmisos
    logger.info("Updating Permissions")
    models = [
        "model_report_backend_invoice_email"
    ]
    load_access_rules_from_model_name(
        cursor, 'som_facturacio_comer', models
    )
    logger.info("Permissions succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
