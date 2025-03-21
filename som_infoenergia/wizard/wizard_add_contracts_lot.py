# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from giscedata_polissa.giscedata_polissa import CONTRACT_STATES
from gestionatr.defs import TABLA_113

STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]


class WizardAddContractsLot(osv.osv_memory):
    _name = "wizard.infoenergia.add.contracts.lot"

    def add_contracts_lot(self, cursor, uid, ids, context=None):

        if not context.get("active_id", False) or len(context.get("active_ids", False)) > 1:
            raise osv.except_osv(_("Error!"), _("S'ha de seleccionar un lot"))

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        pol_obj = self.pool.get("giscedata.polissa")

        wiz = self.browse(cursor, uid, ids[0])
        search_params = []
        search_params_relation = {
            "polissa_state": [("state", "=", wiz.polissa_state)],
            "init_date": [("data_alta", ">=", wiz.init_date)],
            "end_date": [("data_alta", "<=", wiz.end_date)],
            "comer_fare": [("llista_preu", "ilike", "%{}%".format(wiz.comer_fare))],
            "access_fare": [("tarifa", "ilike", "%{}%".format(wiz.access_fare))],
            "autoconsum": [("tipus_subseccio", "!=", "00"), ("tipus_subseccio", "!=", False)]
            if wiz.autoconsum == "all"
            else [("tipus_subseccio", "=", wiz.autoconsum)],
            "tipo_medida": [("tipo_medida", "ilike", "%{}%".format(wiz.tipo_medida))],
            "category": [
                ("category_id", "!=", False),
                ("category_id.name", "ilike", "%{}%".format(wiz.category)),
            ],
        }
        for field in search_params_relation.keys():
            if getattr(wiz, field):
                search_params += search_params_relation[field]
        res_ids = pol_obj.search(cursor, uid, search_params)
        self.write(
            cursor,
            uid,
            ids,
            {
                "state": "finished",
                "len_result": "La cerca ha trobat {} resultats".format(len(res_ids)),
            },
        )
        ctx = {"from_model": "polissa_id"}
        lot_obj.create_enviaments_from_object_list(
            cursor, uid, context.get("active_id"), res_ids, ctx
        )

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard")),
        "polissa_state": fields.selection([(False, "")] + CONTRACT_STATES, _("Estat")),
        "init_date": fields.date(_("Data alta")),
        "end_date": fields.date(_("")),
        "access_fare": fields.char("Tarifa d'accés", size=256),
        "comer_fare": fields.char("Tarifa comercialitzadora", size=256),
        "autoconsum": fields.selection(
            [(False, ""), ("all", "Qualsevol Autoconsum")] + TABLA_113, "Tipus autoconsum"
        ),
        "tipo_medida": fields.char("Tipus Punt", size=256),
        "category": fields.char("Categoria", size=256),
        "len_result": fields.text("Resultat de la cerca", readonly=True),
    }

    _defaults = {"state": "init"}


WizardAddContractsLot()
