# -*- coding: utf-8 -*-
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    # Enllaça update i respecta el valor anterior si existía
    uid = 1

    if installed_version:
        pool = pooler.get_pool(cursor.dbname)
        filter_obj = pool.get("wizard.model.list.from.file.filter")
        filter_ids = filter_obj.search(
            cursor,
            uid,
            [
                ("column", "=", "factura_rectificada"),
                ("model", "=", "giscedata.facturacio.importacio.linia"),
            ],
        )

        if filter_ids:
            filter_obj.unlink(cursor, uid, filter_ids[0])

        load_data_records(
            cursor,
            "som_facturacio_switching",
            "wizard/wizard_model_list_from_file_data.xml",
            ["model_list_wizard_filter_importacio_factura_rectificada"],
            mode="update",
        )


migrate = up
