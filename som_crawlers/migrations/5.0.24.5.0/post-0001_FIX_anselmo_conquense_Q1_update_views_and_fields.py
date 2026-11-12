# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating XML and CSV files")
    data_files = [
        'data/som_crawlers_task_data.xml',
        'data/som_crawlers_step_data.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'som_crawlers', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")

    # Desactivate tasks
    sct_obj = pool.get('som.crawlers.task')
    scts_obj = pool.get('som.crawlers.task.step')
    task_lists_to_deactivate = [
        "descarregar_anselmo",
        "descargar_conquense",
        "descargar_iberdrola_contratacion"
    ]
    imd_obj = pool.get('ir.model.data')
    for task_list in task_lists_to_deactivate:
        task_list_id = imd_obj.get_object_reference(
            cursor, 1, 'som_crawlers', task_list
        )[1]
        task_list = sct_obj.browse(cursor, 1, task_list_id)
        task_list.active = False
        sct_obj.write(cursor, 1, [task_list.id], {
            'active': False
        })
    logger.info("Old tasks deactivated successfully.")

    # Delete objects
    steps_list_to_delete = [
        "pas_descargar_iberdrola_contratacion",
        "pas_descargar_iberdrola_r1",
        "pas_descargar_iberdrola_q1",
        "pas_descargar_iberdrola_f1",
        "pas_descargar_iberdrola_e1",
        "pas_descargar_iberdrola_d1",
        "pas_descargar_iberdrola_t1",
        "pas_importar_anselmo",
        "taskStep_conquense_download",
        "taskStep_conquense_import",
    ]
    for step in steps_list_to_delete:
        logger.info("Deleting {}...".format(step))
        step_id = imd_obj.get_object_reference(
            cursor, 1, 'som_crawlers', step
        )[1]
        scts_obj.unlink(cursor, 1, [step_id])
    logger.info("Old objects deleted successfully.")


def down(cursor, installed_version):
    pass


migrate = up
