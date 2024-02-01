# -*- coding: utf-8 -*-
from osv import fields, osv


_tipus_tarifes_lead = [
    ("tarifa_existent", "Tarifa existent (ATR o Fixa)"),
    ("tarifa_provisional", "Tarifa ATR provisional"),
]


class GiscedataCrmLead(osv.OsvInherits):

    _inherit = "giscedata.crm.lead"

    def contract_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        context["lead"] = True

        lead = self.browse(cursor, uid, ids[0])

        preus_provisional_energia = {
            "P1": lead.preu_fix_energia_p1,
            "P2": lead.preu_fix_energia_p2,
            "P3": lead.preu_fix_energia_p3,
            "P4": lead.preu_fix_energia_p4,
            "P5": lead.preu_fix_energia_p5,
            "P6": lead.preu_fix_energia_p6,
        }
        context["tarifa_provisional"] = {"preus_provisional_energia": preus_provisional_energia}
        if lead.set_custom_potencia:
            preus_provisional_potencia = {
                "P1": lead.preu_fix_potencia_p1,
                "P2": lead.preu_fix_potencia_p2,
                "P3": lead.preu_fix_potencia_p3,
                "P4": lead.preu_fix_potencia_p4,
                "P5": lead.preu_fix_potencia_p5,
                "P6": lead.preu_fix_potencia_p6,
            }
            context["tarifa_provisional"]["preus_provisional_potencia"] = preus_provisional_potencia

        return super(GiscedataCrmLead, self).contract_pdf(cursor, uid, ids, context=context)

    def _check_and_get_mandatory_fields(
        self, cursor, uid, crml_id, mandatory_fields=[], other_fields=[], context=None
    ):
        if not (context is None or context.get("som_from_activation_lead")):
            if "llista_preu" in mandatory_fields:
                data = self.read(cursor, uid, crml_id, ["tipus_tarifa_lead", "set_custom_potencia"])
                if (
                    data["tipus_tarifa_lead"] == "tarifa_provisional"
                    and data["set_custom_potencia"]
                ):
                    mandatory_fields.pop(mandatory_fields.index("llista_preu"))

        return super(GiscedataCrmLead, self)._check_and_get_mandatory_fields(
            cursor, uid, crml_id, mandatory_fields, other_fields, context
        )

    def onchange_tipus_tarifa_lead(self, cursor, uid, ids, tipus_tarifa_lead):
        res = {
            "value": {"set_custom_potencia": False},
            "domain": {},
            "warning": {},
        }
        if tipus_tarifa_lead == "tarifa_provisional":
            res["value"]["llista_preu"] = False
        return res

    def onchange_set_custom_potencia(self, cursor, uid, ids, set_custom_potencia):
        res = {
            "value": {},
            "domain": {},
            "warning": {},
        }
        if set_custom_potencia == True:
            res["value"]["llista_preu"] = False
        else:
            res["value"]["preu_fix_potencia_p1"] = 0
            res["value"]["preu_fix_potencia_p2"] = 0
            res["value"]["preu_fix_potencia_p3"] = 0
            res["value"]["preu_fix_potencia_p4"] = 0
            res["value"]["preu_fix_potencia_p5"] = 0
            res["value"]["preu_fix_potencia_p6"] = 0

        return res

    _columns = {
        "tipus_tarifa_lead": fields.selection(_tipus_tarifes_lead, "Tipus de tarifa del contracte"),
        "set_custom_potencia": fields.boolean("Personalitzar preus potència"),
        "preu_fix_energia_p1": fields.float("Preu Fix Energia P1", digits=(16, 6)),
        "preu_fix_energia_p2": fields.float("Preu Fix Energia P2", digits=(16, 6)),
        "preu_fix_energia_p3": fields.float("Preu Fix Energia P3", digits=(16, 6)),
        "preu_fix_energia_p4": fields.float("Preu Fix Energia P4", digits=(16, 6)),
        "preu_fix_energia_p5": fields.float("Preu Fix Energia P5", digits=(16, 6)),
        "preu_fix_energia_p6": fields.float("Preu Fix Energia P6", digits=(16, 6)),
        "preu_fix_potencia_p1": fields.float("Preu Fix Potència P1", digits=(16, 6)),
        "preu_fix_potencia_p2": fields.float("Preu Fix Potència P2", digits=(16, 6)),
        "preu_fix_potencia_p3": fields.float("Preu Fix Potència P3", digits=(16, 6)),
        "preu_fix_potencia_p4": fields.float("Preu Fix Potència P4", digits=(16, 6)),
        "preu_fix_potencia_p5": fields.float("Preu Fix Potència P5", digits=(16, 6)),
        "preu_fix_potencia_p6": fields.float("Preu Fix Potència P6", digits=(16, 6)),
    }

    _defaults = {
        "tipus_tarifa_lead": lambda *a: "tarifa_existent",
        "set_custom_potencia": lambda *a: False,
    }


GiscedataCrmLead()
