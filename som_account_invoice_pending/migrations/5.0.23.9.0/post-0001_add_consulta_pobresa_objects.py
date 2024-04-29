# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")
    pool = pooler.get_pool(cursor.dbname)

    #  UPDATAR UN MODUL NOU AL CREAR-LO O AFEGIR UNA COLUMNA
    logger.info("Creating table: agrupacio.supramunicipal")
    pool.get("agrupacio.supramunicipal")._auto_init(
        cursor, context={"module": "som_account_invoice_pending"}
    )
    logger.info("Table created succesfully.")

    logger.info("Updating table: 'giscedata.polissa")
    pool.get("giscedata.polissa")._auto_init(
        cursor, context={"module": "som_account_invoice_pending"}
    )
    logger.info("Table created succesfully.")

    logger.info("Creating table: 'som.consulta.pobresa'")
    pool.get("som.consulta.pobresa")._auto_init(
        cursor, context={"module": "som_account_invoice_pending"}
    )
    logger.info("Table created succesfully.")

    logger.info("Creating table: 'wizard.crear.consulta.pobresa'")
    pool.get("wizard.crear.consulta.pobresa")._auto_init(
        cursor, context={"module": "som_account_invoice_pending"}
    )
    logger.info("Table created succesfully.")

    #  UPDATAR UN XML SENCER
    logger.info("Updating XML som_account_invoice_pending/data/agrupacio_supramunicipal_data.xml")
    load_data(
        cursor,
        "som_account_invoice_pending",
        "data/agrupacio_supramunicipal_data.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating XML som_account_invoice_pending/data/som_consulta_pobresa_data.xml")
    load_data(
        cursor,
        "som_account_invoice_pending",
        "data/som_consulta_pobresa_data.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating XML som_account_invoice_pending/views/agrupacio_supramunicipal_view.xml")
    load_data(
        cursor,
        "som_account_invoice_pending",
        "views/agrupacio_supramunicipal_view.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating XML som_account_invoice_pending/views/som_consulta_pobresa_view.xml")
    load_data(
        cursor,
        "som_account_invoice_pending",
        "views/som_consulta_pobresa_view.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Updating XML som_account_invoice_pending/wizard/wizard_crear_consulta_pobresa.xml")
    load_data(
        cursor,
        "som_account_invoice_pending",
        "wizard/wizard_crear_consulta_pobresa.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")

    #  UPDATAR UNA PART DE L'XML (POSAR LA ID)
    list_of_records = ["som_account_invoice_pending.pendent_consulta_probresa_pending_state"]
    load_data_records(
        cursor,
        'som_account_invoice_pending',
        'data/som_account_invoice_pending_data.xml',
        list_of_records,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")

    #  UPDATAR ACCESS RULES
    logger.info("Loading Acces Rules...")
    load_data(cursor, "som_account_invoice_pending", "security/ir.model.access.csv", mode="update")
    logger.info("Access rules create success!")


def down(cursor, installed_version):
    pass


migrate = up
