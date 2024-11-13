# -*- coding: utf-8 -*-
import logging
import pooler
from tools import config
from oopgrade.oopgrade import add_columns_fk, column_exists, load_data
from tqdm import tqdm


def search_email(pool, cursor, uid, fact_id, fact_number, sent_date):
    mail_obj = pool.get("poweremail.mailbox")

    query = [
        ('folder', '=', 'sent'),
        ('reference', '=', 'giscedata.facturacio.factura,{}'.format(fact_id)),
        ('date_mail', '=', sent_date),
    ]

    subjects = [
        u'Factura XX',
        u'Som Energia: Factura XX',
        u'Factura pagada XX',
        u'Factura electricitat XX',
        u'Factura electricidad XX',
        u'Reenviament XX (adjunt correcte) / Reenvío XX (adjunto correcto)',
        u'Reenvío de factura XX',
        u'Reenviament Factura XX',
        u'Reenvío Factura XX',
    ]

    # Let's try the fastest ones
    for subject in subjects:
        full_subject = subject.replace("XX", fact_number)
        mail_ids = mail_obj.search(
            cursor, uid,
            [('pem_subject', '=', full_subject)] + query
        )
        if mail_ids:
            return mail_ids

    # The slowest one
    return mail_obj.search(
        cursor, uid,
        [('pem_subject', 'like', '%{}%'.format(fact_number))] + query
    )


def update_field(pool, cursor, uid, fact_id):
    fact_obj = pool.get("giscedata.facturacio.factura")

    fact_data = fact_obj.read(cursor, uid, ['number', 'enviat_data'])

    mail_ids = search_email(pool, cursor, uid, fact_id,
                            fact_data['number'], fact_data['enviat_data'])
    if mail_ids:
        fact_obj.write(cursor, uid, fact_id, {'enviat_mail_id': mail_ids[0]})


def get_fact_to_update(pool, cursor, uid):
    fact_obj = pool.get("giscedata.facturacio.factura")
    fact_ids = fact_obj.search(cursor, uid, [
        ('number', '!=', None),
        ('enviat', '=', True),
        ('enviat_carpeta', '=', 'sent'),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])
    return fact_ids


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Create enviat_mail_id column  in giscedata_facturacio_factura")
    if not column_exists(cursor, 'giscedata_facturacio_factura', 'enviat_mail_id'):
        new_column_spec = [('enviat_mail_id', 'int', 'poweremail_mailbox', 'id', 'set null')]
        add_columns_fk(cursor, {'giscedata_facturacio_factura': new_column_spec})
        logger.info("Column created succesfully.")
    else:
        logger.info("Column already created!!.")

    logger.info("Updating giscedata_facturacio_factura.xml")
    load_data(
        cursor,
        'giscedata_facturacio_comer_som',
        'giscedata_facturacio_factura.xml',
        idref=None,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")

    logger.info("Starting the migration: Fill the column")
    uid = 1
    fact_ids = get_fact_to_update(pool, cursor, uid)
    for fact_id in tqdm(fact_ids):
        update_field(pool, cursor, uid, fact_id)
    logger.info("Column succesfuly filled")


def down(cursor, installed_version):
    pass


migrate = up
