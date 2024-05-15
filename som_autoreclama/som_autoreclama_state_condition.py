# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomAutoreclamaStateCondition(osv.osv):

    _name = "som.autoreclama.state.condition"
    _rec_name = "subtype_id"
    _order = "priority"

    CONDITION_CODE = [
        ("ATC", _("Dies per subtipus ATC")),
        ("noF1", _("Falta F1 a pòlissa")),
        ("F1ok", _("F1 a data correcta a pòlissa")),
        ("CACR1006closed", _("Dies des de ATC R1 006 actual tancat")),
        ("oldPolissa", _("Polissa de baixa x dies o baixa facturada")),
        ("2_006_in_a_row", _("Dues 006 seguides en X dies")),
    ]

    def fit_condition(self, cursor, uid, id, data, namespace, context=None):
        if namespace == "polissa":
            cond_data = self.read(cursor, uid, id, ["days", "condition_code"], context=context)
            if cond_data['condition_code'] == 'noF1':
                return data["days_without_F1"] > cond_data["days"]
            if cond_data['condition_code'] == 'F1ok':
                return data["days_without_F1"] <= cond_data["days"]
            if cond_data['condition_code'] == 'CACR1006closed':
                return data["days_since_current_CACR1006_closed"] > cond_data["days"]
            if cond_data['condition_code'] == 'oldPolissa':
                return data["days_since_baixa"] >= cond_data["days"] or data["baixa_facturada"]
            if cond_data['condition_code'] == '2_006_in_a_row':
                return False
        if namespace == "atc":
            cond_data = self.read(cursor, uid, id, ["subtype_id", "days"], context=context)
            return (
                data["subtipus_id"] == cond_data["subtype_id"][0]
                and data["distri_days"] >= cond_data["days"]
                and data["agent_actual"] == "10"
                and data["state"] == "pending"
            )
        return False

    _columns = {
        "priority": fields.integer(_("Order"), required=True),
        "active": fields.boolean(string=_(u"Activa"), help=_(u"Indica si la condició esta activa")),
        "condition_code": fields.selection(CONDITION_CODE, "Condició", required=True),
        "subtype_id": fields.many2one(
            "giscedata.subtipus.reclamacio",
            _(u"Subtipus"),
            required=False,
            help=_(u"Subtipus de la reclamació associada al cas ATC"),
        ),
        "days": fields.integer(
            _(u"Dies d'espera"), required=True, help=_(u"Dies sense resposta de la distribuïdora")
        ),
        "state_id": fields.many2one("som.autoreclama.state", _(u"Estat actual"), required=True),
        "next_state_id": fields.many2one(
            "som.autoreclama.state", _(u"Estat següent"), required=True
        ),
    }

    _defaults = {}


SomAutoreclamaStateCondition()
