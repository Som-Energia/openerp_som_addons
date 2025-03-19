from oopgrade import DataMigration
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <openerp>
        <data noupdate="1">
            <record model="giscedata.polissa.category"
                id="som_sw_reclamacions_lectura_en_curs">
                <field name="name">En curs</field>
                <field name="parent_id" ref="cat_1"/>
                <field name="active">True</field>
            </record>
        </data>
    </openerp>
    """

    logger = logging.getLogger("openerp.migration")
    logger.info("Migrating data from giscedata_polissa_category")

    dm = DataMigration(
        xml_content,
        cursor,
        "som_polissa_soci",
        search_params={"giscedata.polissa.category": ["name"]},
    )
    dm.migrate()


def down(cursor, installed_version):
    pass


migrate = up
