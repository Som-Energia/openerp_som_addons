# -*- coding: utf-8 -*-
from datetime import datetime
from osv import fields, osv
from tools.translate import _
import xml.etree.ElementTree as ET


class WizardSubtypeR1(osv.osv_memory):
    """Wizard to generate R1."""

    _name = "wizard.subtype.r1"
    _inherit = "wizard.subtype.r1"

    def default_get(self, cursor, uid, fields, context=None):
        if context is None:
            context = {}

        res = super(WizardSubtypeR1, self).default_get(cursor, uid, fields, context)

        if len(fields) == 2 and fields[0] == "tipus" and fields[1] == "subtipus_id":
            return res

        if (
            "extra_values" in context
            and "ref_model" in context["extra_values"]
            and context["extra_values"]["ref_model"] == "giscedata.atc"
            and "ref_id" in context["extra_values"]
        ):
            atc_obj = self.pool.get("giscedata.atc")
            atc_channel_data = atc_obj.read(
                cursor, uid, context["extra_values"]["ref_id"][0], ["canal_id"]
            )
            atc_channel_id = atc_channel_data["canal_id"][0]
            if atc_channel_id in [1, 2, 3, 4]:
                res["tipus_reclamant"] = "01"
        return res

    def action_create_r1_case_from_dict(self, cursor, uid, polissa_id, dict_fields, context=None):
        # Els hem de borrar perque a dins del create_r1 es fa un write directe
        # d'aquest diccionari a un r1.01
        dict_fields2 = dict_fields.copy()
        if "facturacio_suspesa" in dict_fields2.keys():
            dict_fields2.pop("facturacio_suspesa")
        if "refacturacio_pendent" in dict_fields2.keys():
            dict_fields2.pop("refacturacio_pendent")
        res = super(WizardSubtypeR1, self).action_create_r1_case_from_dict(
            cursor, uid, polissa_id, dict_fields2, context=context
        )
        if not isinstance(res[-1], long):
            return res

        pol_obj = self.pool.get("giscedata.polissa")
        subtipus_obj = self.pool.get("giscedata.subtipus.reclamacio")
        user_obj = self.pool.get("res.users")
        sw_obj = self.pool.get("giscedata.switching")

        subtipus_info = subtipus_obj.read(
            cursor, uid, dict_fields.get("subtipus_id"), ["name", "type"]
        )
        if not subtipus_info:
            return res

        if subtipus_info["type"] != "02":
            return res

        pinf = pol_obj.read(cursor, uid, polissa_id, ["observacions", "category_id"])

        # Escriure al contracte el comentari:
        # "Data_Usuari_Reclamació (codi Cas) SUBTIPUS. Generat el pas R1-01”
        subtipus_info_str = "{0}-{1}".format(subtipus_info["type"], subtipus_info["name"])
        user_name = user_obj.read(cursor, uid, uid, ["name"])["name"]
        sw_code = sw_obj.read(cursor, uid, res[-1], ["codi_sollicitud"])["codi_sollicitud"]
        new_text = _(u"{0}, {1}, Reclamació {2}: SUBTIPUS {3}. Generat el pas R1-01\n\n").format(
            datetime.today().strftime("%d-%m-%Y"), user_name, sw_code, subtipus_info_str
        )

        # Activar categoria “Reclamacions lectura / en curs”
        imd_obj = self.pool.get("ir.model.data")
        categoria_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa_soci", "som_sw_reclamacions_lectura_en_curs"
        )[1]
        category_ids = pinf["category_id"]

        # Asignar al responsable genèric
        if subtipus_info["name"] not in ["003", "004", "010", "057", "067"]:
            responsable = user_obj.search(cursor, uid, [("login", "=", "r1manager")])
            if len(responsable):
                sw_obj.write(cursor, uid, res[-1], {"user_id": responsable[0]})

        pol_vals = {
            "observacions": new_text + (pinf["observacions"] or ""),
            "category_id": [(6, 0, category_ids + [categoria_id])],
        }

        if dict_fields.get("facturacio_suspesa", False):
            pol_vals.update(
                {
                    "facturacio_suspesa": True,
                    "observacio_suspesa": new_text.replace("\n", ""),
                }
            )
        if dict_fields.get("refacturacio_pendent", False):
            pol_vals.update({"refacturacio_pendent": True})

        pol_obj.write(cursor, uid, polissa_id, pol_vals)

        return res

    def fields_view_get(
        self, cursor, uid, view_id=None, view_type="form", context=None, toolbar=False
    ):
        res = super(WizardSubtypeR1, self).fields_view_get(
            cursor, uid, view_id, view_type, context=context, toolbar=toolbar
        )
        # Afegim facturacio_suspesa i refacturacio_pendent a les vistes
        root = ET.fromstring(res["arch"])
        button_create = root.findall("group")[0].findall("button")[0]
        for btn in root.findall("group")[0].findall("button"):
            if btn.get("string") == "Crear Cas":
                button_create = btn
        button_create.attrib.update(
            {
                "confirm": "Aquesta acció generarà casos R1. Has revisat l'estat de "
                "la facturació suspesa i la refacturació pendent abans de continuar?"
            }
        )

        notebook = root.find("notebook")
        current_page = notebook.findall("page")[0]
        for page in notebook.findall("page"):
            if page.get("string") == "Dades Sol.licitud":
                current_page = page
        # Add the field to the page
        attrs = {"string": "Marcar facturacio suspesa: ", "colspan": "2"}
        ET.SubElement(current_page, "separator", attrs)
        attrs = {"name": "facturacio_suspesa", "nolabel": "1"}
        ET.SubElement(current_page, "field", attrs)
        attrs = {"string": "Marcar refacturacio pendent: ", "colspan": "2"}
        ET.SubElement(current_page, "separator", attrs)
        attrs = {"name": "refacturacio_pendent", "nolabel": "1"}
        ET.SubElement(current_page, "field", attrs)
        res["arch"] = ET.tostring(root)
        return res

    def _default_facturacio_suspesa(self, cursor, uid, context=None):
        subtipus_obj = self.pool.get("giscedata.subtipus.reclamacio")
        subtipus = subtipus_obj.browse(cursor, uid, context.get("subtipus_id"))
        return subtipus.name in ["036", "009"]

    def _default_refacturacio_pendent(self, cursor, uid, context=None):
        subtipus_obj = self.pool.get("giscedata.subtipus.reclamacio")
        subtipus = subtipus_obj.browse(cursor, uid, context.get("subtipus_id"))
        return subtipus.name in ["036", "009"]

    _columns = {
        "facturacio_suspesa": fields.boolean("Marcar contracte amb facturació suspesa"),
        "refacturacio_pendent": fields.boolean("Marcar contracte amb refacturacio pendent"),
    }

    _defaults = {
        "facturacio_suspesa": _default_facturacio_suspesa,
        "refacturacio_pendent": _default_refacturacio_pendent,
    }


WizardSubtypeR1()
