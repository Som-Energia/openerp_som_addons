# coding=utf-8
import logging
from oopgrade.oopgrade import load_data_records, load_data, add_columns_fk


def up(cursor, installed_version):
    if not installed_version:
        return

    import pooler

    logger = logging.getLogger("openerp.migration")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Setting up powersms provider DB...")
    pool.get("powersms.provider")._auto_init(cursor, context={"module": "powersms"})
    logger.info("TABLE powersms_provider CREATED success!")

    logger.info("Adding FK provider_id on powersms_core_accounts...")
    add_columns_fk(
        cursor,
        {"powersms_core_accounts": [("provider_id", "int", "powersms_provider", "id", "SET NULL")]},
    )
    logger.info("FK provider_id created!")

    logger.info("Loading Providers from data...")
    load_data_records(
        cursor, "powersms", "powersms_provider_data.xml", ["powersms_provider_lleidanet"]
    )
    load_data_records(cursor, "powersms", "powersms_core_view.xml", ["powersms_core_accounts_form"])
    load_data_records(cursor, "powersms", "powersms_core_view.xml", ["powersms_core_accounts_tree"])

    logger.info("Provider data loaded!")

    logger.info("Setting lleida as default for all existing accounts")
    set_lleidanet_for_existing_accounts = """
    UPDATE powersms_core_accounts set provider_id = (
        SELECT id FROM powersms_provider WHERE function_pattern_code = 'lleida'
    )
    """
    cursor.execute(set_lleidanet_for_existing_accounts)

    logger.info("Loading Acces Rules...")
    load_data(cursor, "powersms", "security/ir.model.access.csv", mode="update")
    logger.info("Access rules create success!")


def down(cursor, installed_version):
    if not installed_version:
        return


migrate = up
