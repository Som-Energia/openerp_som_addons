# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    wiz_obj = pool.get('wizard.add.cut.off.to.polissa.from.csv')
    wiz_obj._auto_init(cursor, context={'module': 'som_polissa'})

    logger.info("Updating XMLs")
    xmls = [
        "wizard/wizard_add_cut_off_to_polissa_from_csv_view.xml",
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
