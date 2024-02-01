# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class WizardCreateAtc(osv.osv_memory):

    _inherit = "wizard.create.atc.from.polissa"

    def create_atc_case(self, cursor, uid, ids, from_model, context=None):

        if context is None:
            context = {}
        res = super(WizardCreateAtc, self).create_atc_case(
            cursor, uid, ids, from_model, context=context
        )
        wizard = self.browse(cursor, uid, ids[0], context)
        atc_obj = self.pool.get("giscedata.atc")
        for atc_id in wizard.generated_cases:
            if wizard.tag:
                atc_obj.write(cursor, uid, atc_id, {"tag": wizard.tag.id})
        return res

    def onchange_subtipus(self, cursor, uid, ids, subtipus_id):

        res = super(WizardCreateAtc, self).onchange_subtipus(cursor, uid, ids, subtipus_id)
        section_id = res["value"]["section_id"]
        seccio = False
        mostrar_tag = False
        factura_tag = False

        section_obj = self.pool.get("crm.case.section")
        if section_id:
            seccio = section_obj.read(cursor, uid, section_id, ["code"])["code"]
        if seccio:
            if seccio == "ATCF" or seccio == "ATCC" or seccio == "ATCR" or seccio == "ATCCB":
                mostrar_tag = True
            else:
                mostrar_tag = False
            factura_tag = True if seccio == "ATCF" else False
        res["value"]["mostrar_tag"] = mostrar_tag
        res["value"]["factura_tag"] = factura_tag
        return res

    def onchange_section(self, cursor, uid, ids, section_id):
        res = False
        mostrar_tag = False
        factura_tag = False
        section_obj = self.pool.get("crm.case.section")
        seccio = section_obj.read(cursor, uid, section_id, ["code"])["code"]
        if seccio:
            if seccio == "ATCF" or seccio == "ATCC" or seccio == "ATCR" or seccio == "ATCCB":
                mostrar_tag = True
            else:
                mostrar_tag = False
            factura_tag = True if seccio == "ATCF" else False
        return {
            "value": {"mostrar_tag": mostrar_tag, "factura_tag": factura_tag},
            "domain": {},
            "warning": {},
        }

    _columns = {
        "tag": fields.many2one("giscedata.atc.tag", "Etiqueta"),
        "mostrar_tag": fields.boolean(u"Mostrar_tag"),
        "factura_tag": fields.boolean(u"factura_tag"),
    }
    _defaults = {
        "mostrar_tag": lambda *a: False,
    }


WizardCreateAtc()
