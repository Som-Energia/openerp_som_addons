# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records, delete_record


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")

    list_of_records = ["common_template_rejection_footer",
                       "common_template_rejection_text_ca",
                       "common_template_rejection_text_es"]
    delete_record(
        cursor,
        'som_poweremail_common_templates',
        list_of_records,
    )

    list_of_records = ["common_template_modi_rejection_text",
                       "common_template_rejection_text"]
    load_data_records(
        cursor,
        'som_poweremail_common_templates',
        'commontemplates_data.xml',
        list_of_records,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
