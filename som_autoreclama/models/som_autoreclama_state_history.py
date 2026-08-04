# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import date


class SomAutoreclamaStateHistory(osv.osv):

    _name = "som.autoreclama.state.history"

    def get_this_model(self, cursor, uid, context=None):
        return self.pool.get("som.autoreclama.state.history.{}".format(self._namespace))

    def historize(
        self, cursor, uid, item_id, next_state_id, current_date, generated_atc_id, context=None
    ):
        if not current_date:
            current_date = date.today().strftime("%Y-%m-%d")

        h_ids = self.search(
            cursor,
            uid,
            [
                (self._field_ref, "=", item_id),
                ("end_date", "=", False),
            ],
            context=context,
        )
        if h_ids:
            self.write(cursor, uid, h_ids, {"end_date": current_date}, context=context)

        new_atc = {
            self._field_ref: item_id,
            "state_id": next_state_id,
            "change_date": current_date,
            "end_date": False,
        }
        if generated_atc_id:
            new_atc["generated_atc_id"] = generated_atc_id

        return self.create(cursor, uid, new_atc, context=context)


SomAutoreclamaStateHistory()


class SomAutoreclamaStateHistoryAtc(SomAutoreclamaStateHistory):

    _name = "som.autoreclama.state.history.atc"
    _namespace = "atc"
    _field_ref = "atc_id"

    _columns = {
        "state_id": fields.many2one("som.autoreclama.state", _(u"State"), required=False),
        "change_date": fields.date(_(u"Change Date"), select=True, readonly=True),
        "end_date": fields.date(_(u"End Date"), select=True, readonly=True),
        "atc_id": fields.many2one("giscedata.atc", _(u"ATC"), readonly=True, ondelete="set null"),
        "generated_atc_id": fields.many2one(
            "giscedata.atc", _(u"Cas ATC generat"), readonly=True, ondelete="set null"
        ),
    }
    _order = "end_date desc, id desc"


SomAutoreclamaStateHistoryAtc()


class SomAutoreclamaStateHistoryPolissa(SomAutoreclamaStateHistory):

    _name = "som.autoreclama.state.history.polissa"
    _namespace = "polissa"
    _field_ref = "polissa_id"

    _columns = {
        "state_id": fields.many2one("som.autoreclama.state", _(u"State"), required=False),
        "change_date": fields.date(_(u"Change Date"), select=True, readonly=True),
        "end_date": fields.date(_(u"End Date"), select=True, readonly=True),
        "polissa_id": fields.many2one(
            "giscedata.polissa",
            _(u"Polissa"),
            readonly=True,
            ondelete="set null",
        ),
        "generated_atc_id": fields.many2one(
            "giscedata.atc", _(u"Cas ATC generat"), readonly=True, ondelete="set null"
        ),
    }
    _order = "end_date desc, id desc"


SomAutoreclamaStateHistoryPolissa()


class SomAutoreclamaStateHistoryPolissa009(SomAutoreclamaStateHistory):

    _name = "som.autoreclama.state.history.polissa009"
    _namespace = "polissa009"
    _field_ref = "polissa_id"

    _columns = {
        "state_id": fields.many2one("som.autoreclama.state", _(u"State"), required=False),
        "change_date": fields.date(_(u"Change Date"), select=True, readonly=True),
        "end_date": fields.date(_(u"End Date"), select=True, readonly=True),
        "polissa_id": fields.many2one(
            "giscedata.polissa",
            _(u"Polissa"),
            readonly=True,
            ondelete="set null",
        ),
        "generated_atc_id": fields.many2one(
            "giscedata.atc", _(u"Cas ATC generat"), readonly=True, ondelete="set null"
        ),
    }
    _order = "end_date desc, id desc"


SomAutoreclamaStateHistoryPolissa009()
