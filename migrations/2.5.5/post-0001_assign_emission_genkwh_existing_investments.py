# coding=utf-8
import pooler
import netsvc

from addons.gisceupgrade_migratoor.gisceupgrade_migratoor import log

version = "somenergia-generationkwh_2.5.5: "


def migrate(cursor, installed_version):
    """Assigna emissio a inversions generation existents
    """
    uid = 1
    pool = pooler.get_pool(cursor.dbname)


    # evitar creació constraint consum_positiu
    imd_obj = pool.get('ir.model.data')
    emission_id = imd_obj.get_object_reference(cursor, uid,
            'som_generationkwh','emissio_genkwh')[1]

    cursor.execute("UPDATE generationkwh_investment"
                   " SET emission_id = " + str(emission_id) + 
                   " WHERE emission_id IS NULL AND name ilike 'GKWH%'")



def up(cursor, installed_version):
    pass

def down(cursor):
    pass

# vim: ts=4 sw=4 et
