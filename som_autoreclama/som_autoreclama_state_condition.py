# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomAutoreclamaStateCondition(osv.osv):

    _name = "som.autoreclama.state.condition"
    _rec_name = "subtype_id"
    _order = "priority"

    def fit_condition(self, cursor, uid, id, data, namespace, context=None):
        if namespace == "polissa":
            cond_data = self.read(cursor, uid, id, ["days"], context=context)
            return data["days_without_F1"] >= cond_data["days"]
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
