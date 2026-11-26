# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv
from tools.translate import _


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


class GiscedataSwitchingR1_04(osv.osv):
    _name = "giscedata.switching.r1.04"
    _inherit = "giscedata.switching.r1.04"

    def create(self, cursor, uid, vals, context=None):
        # La creació inicial automàtica encara no inclou els comentaris.
        if "comentaris" in vals:
            self.check_comments(vals["comentaris"])
        return super(GiscedataSwitchingR1_04, self).create(
            cursor, uid, vals, context=context
        )

    def write(self, cursor, uid, ids, vals, context=None):
        if "comentaris" in vals:
            self.check_comments(vals["comentaris"])
        elif list(vals) != ["sw_id"]:
            # step.info enllaça el pas amb el cas abans d'editar el formulari.
            steps = self.read(cursor, uid, ids, ["comentaris"], context=context)
            if isinstance(steps, dict):
                steps = [steps]
            for step in steps:
                self.check_comments(step["comentaris"])
        return super(GiscedataSwitchingR1_04, self).write(
            cursor, uid, ids, vals, context=context
        )

    def generar_xml(self, cursor, uid, pas_id, context=None):
        if pas_id:
            step_id = pas_id[0] if isinstance(pas_id, (list, tuple)) else pas_id
            step = self.read(cursor, uid, step_id, ["comentaris"], context=context)
            self.check_comments(step["comentaris"])
        return super(GiscedataSwitchingR1_04, self).generar_xml(
            cursor, uid, pas_id, context=context
        )

    def check_comments(self, comments):
        if not (comments or "").strip():
            raise osv.except_osv(
                _(u"Atenció"),
                _(u"Cal omplir el camp Comentaris del pas 04 de la R1 "
                  u"abans de desar-lo o exportar-lo."),
            )


GiscedataSwitchingR1_04()
