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
        context["lang"] = lead.lang

        preus_provisional_energia = {
            "P1": lead.preu_fix_energia_p1,
            "P2": lead.preu_fix_energia_p2,
            "P3": lead.preu_fix_energia_p3,
            "P4": lead.preu_fix_energia_p4,
            "P5": lead.preu_fix_energia_p5,
            "P6": lead.preu_fix_energia_p6,
        }
        if lead.tipus_tarifa_lead == 'tarifa_provisional':
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
                context["tarifa_provisional"]["preus_provisional_potencia"] = \
                    preus_provisional_potencia

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

    def create_entity_polissa(self, cursor, uid, crml_id, context=None):
        res = super(GiscedataCrmLead, self).create_entity_polissa(
            cursor, uid, crml_id, context=context
        )
        values = {}
        partner_o = self.pool.get("res.partner")

        # recuperem la polissa recent creada del lead
        lead_vals = self.read(
            cursor, uid, crml_id, ['polissa_id', 'member_number'],
            context=context
        )

        polissa_id = lead_vals["polissa_id"][0]
        member_number = lead_vals["member_number"]

        values["soci"] = partner_o.search(cursor, uid, [("ref", "=", member_number)], limit=1)[0]

        polissa_o = self.pool.get("giscedata.polissa")
        polissa = polissa_o.browse(cursor, uid, polissa_id, context=context)
        if polissa.mode_facturacio != 'atr':
            values['mode_facturacio_generacio'] = polissa.mode_facturacio

        fp_id = polissa_o.calculate_fiscal_position_from_cups(
            cursor, uid,
            polissa.cups.id,
            polissa.cnae.name,
            [potencia.potencia for potencia in polissa.potencies_periode],
            context=context
        )
        if fp_id:
            values['fiscal_position_id'] = fp_id

        if values:
            polissa_o.write(cursor, uid, polissa_id, values, context=context)
        return res

    def onchange_set_custom_potencia(self, cursor, uid, ids, set_custom_potencia):
        res = {
            "value": {},
            "domain": {},
            "warning": {},
        }
        if set_custom_potencia == True:   # noqa: E712
            res["value"]["llista_preu"] = False
        else:
            res["value"]["preu_fix_potencia_p1"] = 0
            res["value"]["preu_fix_potencia_p2"] = 0
            res["value"]["preu_fix_potencia_p3"] = 0
            res["value"]["preu_fix_potencia_p4"] = 0
            res["value"]["preu_fix_potencia_p5"] = 0
            res["value"]["preu_fix_potencia_p6"] = 0

        return res

    def create_entity_titular(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}

        partner_o = self.pool.get("res.partner")

        lead_vals = self.read(
            cursor, uid, crml_id,
            ['owner_is_member', 'persona_firmant_vat', 'persona_nom'],
            context=context
        )

        if lead_vals['owner_is_member']:
            context["create_member"] = True

        if lead_vals['persona_firmant_vat']:
            if len(lead_vals.get("persona_firmant_vat")) <= 9:
                lead_vals['persona_firmant_vat'] = "ES" + lead_vals['persona_firmant_vat']
            lead_vals['persona_firmant_vat'] = lead_vals['persona_firmant_vat'].upper()
            representant_id = partner_o.create(
                cursor, uid, {
                    "vat": lead_vals['persona_firmant_vat'],
                    "name": lead_vals['persona_nom'],
                },
                context=context
            )
            context["partner_representant_id"] = representant_id

        return super(GiscedataCrmLead, self).create_entity_titular(
            cursor, uid, crml_id, context=context
        )

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        seq_o = self.pool.get("ir.sequence")

        if vals.get("owner_is_member"):
            vals['member_number'] = seq_o.get_next(cursor, uid, 'res.partner.soci')

        lead_id = super(GiscedataCrmLead, self).create(cursor, uid, vals, context=context)

        return lead_id

    def create_partner(self, cursor, uid, create_vals, crml_id, context=None):
        if context is None:
            context = {}

        member_o = self.pool.get("somenergia.soci")

        if context.get("create_member"):
            create_vals['ref'] = self.read(
                cursor, uid, crml_id, ["member_number"], context=context
            )["member_number"]

        if context.get("partner_representant_id"):
            create_vals["representante_id"] = context["partner_representant_id"]

        partner_id = super(GiscedataCrmLead, self).create_partner(
            cursor, uid, create_vals, crml_id, context=context)

        if context.get("create_member"):
            member_o.create_one_soci(cursor, uid, partner_id, context=context)

        return partner_id

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
        "member_number": fields.char('Número de sòcia', size=64),
        "owner_is_member": fields.boolean("Mateixa sòcia que titular"),
    }

    _defaults = {
        "tipus_tarifa_lead": lambda *a: "tarifa_existent",
        "set_custom_potencia": lambda *a: False,
    }


GiscedataCrmLead()
