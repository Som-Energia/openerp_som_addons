# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataSwitchingR1_01(osv.osv):
    """Classe pel pas 01"""

    _name = "giscedata.switching.r1.01"
    _inherit = "giscedata.switching.r1.01"

    def update_contract(self, cursor, uid, pas_id, context=None):
        if context is None:
            context = {}
        super(GiscedataSwitchingR1_01, self).update_contract(cursor, uid, pas_id, context=context)

        pas_obj = self.pool.get("giscedata.switching.r1.01")
        pas = pas_obj.browse(cursor, uid, pas_id, context=context)
        polissa = pas.header_id.sw_id.cups_polissa_id

        polisses_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        categoria_xml_id = "som_sw_reclamacions_lectura_en_curs"
        categoria_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa_soci", categoria_xml_id
        )[1]
        categories_ids = [c.id for c in polissa.category_id]
        categories_ids.append(categoria_id)
        categories_ids = list(set(categories_ids))

        polisses_obj.write(
            cursor,
            uid,
            [polissa.id],
            {
                "user_id": uid,
                "category_id": [(6, 0, categories_ids)],
            },
        )
        if context.get("suspesa"):
            polisses_obj.write(
                cursor,
                uid,
                [polissa.id],
                {
                    "facturacio_suspesa": True,
                    "refacturacio_pendent": True,
                },
            )

        if pas.subtipus_id.name not in ["003", "004", "010", "057", "067"]:
            sw_obj = self.pool.get("giscedata.switching")
            user_obj = self.pool.get("res.users")
            responsable = user_obj.search(cursor, uid, [("login", "=", "r1manager")])
            if len(responsable):
                sw_obj.write(cursor, uid, pas.sw_id.id, {"user_id": responsable[0]})


GiscedataSwitchingR1_01()
