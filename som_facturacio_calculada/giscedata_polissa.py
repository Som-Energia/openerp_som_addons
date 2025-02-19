# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime, timedelta
from tools.translate import _
from oorq.decorators import job


class GiscedataPolissaCalculada(osv.osv):
    """
    Pòlissa per afegir les funcions per a la facturació calculada
    """

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def retrocedir_lot(self, cursor, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        lot_o = self.pool.get("giscedata.facturacio.lot")

        last_lot_id = lot_o.search(cursor, uid, [("state", "=", "obert")])[0]

        wiz_retrocedir_o = self.pool.get("wizard.move.contracts.prev.lot")
        ctx = {"incrementar_n_retrocedir": False}
        for _id in ids:

            lot_id = self.read(cursor, uid, _id, ["lot_facturacio"], context)["lot_facturacio"][0]
            if lot_id > last_lot_id:
                wiz_id = wiz_retrocedir_o.create(cursor, uid, {}, context=context)
                wiz_retrocedir_o.move_one_contract_to_prev_lot(
                    cursor, uid, [wiz_id], _id, context=ctx
                )

    def _check_conditions_polissa_calculades(self, cursor, uid, id, context):
        if isinstance(id, (tuple, list)):
            id = id[0]
        imd_o = self.pool.get("ir.model.data")
        cat_id = imd_o.get_object_reference(
            cursor, uid, "som_facturacio_calculada", "cat_gp_factura_calc"
        )[1]

        pol = self.browse(cursor, uid, id)
        if not pol.category_id or cat_id not in [x.id for x in pol.category_id]:
            return False, _(u"no té categoria")
        if pol.tarifa.name != "2.0TD":
            return False, _(u"no es 2.0TD")
        if pol.te_assignacio_gkwh:
            return False, _(u"té GenerationKWh")
        if pol.tipus_autoconsum != "00":
            return False, _(u"té Autoconsum")
        if pol.facturacio_potencia == "max":  # != 'icp'
            return False, _(u"té Maximetre")
        if pol.tg != "1":
            return False, _(u"no té telegestió")
        if pol.cnae.name != "9820":
            return False, _(u"no es un CNAE acceptat")
        gp_cat_o = self.pool.get("giscedata.polissa.category")
        gp_pobresa_id = gp_cat_o.search(cursor, uid, [("name", "ilike", "%Pobresa Energ%")])
        if gp_pobresa_id and pol.category_id and gp_pobresa_id in [x.id for x in pol.category_id]:
            return False, _(u"té Pobresa Energètica")

        return True, _(u"ok")

    def _check_conditions_lectures_calculades(self, cursor, uid, _id, context):
        def add_days(the_date, d):
            return (datetime.strptime(the_date, "%Y-%m-%d") + timedelta(days=d)).strftime(
                "%Y-%m-%d"
            )

        def today_str():
            return datetime.today().strftime("%Y-%m-%d")

        mtr_o = self.pool.get("giscedata.lectures.comptador")
        sw_o = self.pool.get("giscedata.switching")
        imd_o = self.pool.get("ir.model.data")
        lc_origin = imd_o.get_object_reference(
            cursor, uid, "som_facturacio_calculada", "origen_lect_calculada"
        )[1]

        if isinstance(_id, (tuple, list)):
            _id = _id[0]

        pol = self.browse(cursor, uid, _id, context)

        if not pol.data_ultima_lectura:
            return False, _(u"sense data ultima lectura")

        if add_days(pol.data_ultima_lectura, 7) > today_str():
            return False, _(u"lectures a futur")

        mtr_ids = mtr_o.search(cursor, uid, [("polissa.id", "=", _id), ("active", "=", True)])
        if not mtr_ids:
            return False, _(u"no té comptador actiu")

        if len(mtr_ids) != 1:
            return False, _(u"té multiples comptadors actius")

        mtr_id = mtr_ids[0]
        mtr = mtr_o.browse(cursor, uid, mtr_id)
        data_ultima_lectura_lectures = mtr.lectures[0].name

        data_ultima_lectura_factura = pol.data_ultima_lectura_f1
        for lect in mtr.lectures:
            if lect.origen_id.id != lc_origin:
                data_ultima_lectura_factura = lect.name
                break

        data_ultima_lectura_factura_21 = add_days(data_ultima_lectura_factura, 21)
        if data_ultima_lectura_lectures >= data_ultima_lectura_factura_21:
            return False, _(
                u", data de lectura calculada ({}) igual o major a data d'ultima factura no calculada + 21 ({})".format(  # noqa: E501
                    data_ultima_lectura_lectures, data_ultima_lectura_factura_21
                )
            )

        if pol.modcontractual_activa.data_inici > pol.data_ultima_lectura_f1:
            return False, _(u" data d'inici de la modcon activa més gran que data de últim F1")

        sw_ids = sw_o.search(
            cursor,
            uid,
            [
                ("cups_polissa_id", "=", _id),
                ("finalitzat", "=", False),
                ("proces_id.name", "!=", "R1"),
            ],
        )
        if sw_ids:
            return False, _(u" te algun cas ATR no finalitzat")

        return True, _(u" ok")

    def crear_lectura_data(
        self, cursor, uid, _id, measure_date, start_date, mtr_id, lc_origin, context=None
    ):
        wiz_measures_curve_o = self.pool.get("wizard.measures.from.curve")

        vals = {
            "measure_origin": lc_origin,
            "insert_reactive": False,
            "insert_maximeters": False,
            "measure_date": measure_date,
            "start_date": start_date,
            "meter_id": mtr_id,
        }
        ctx = {
            "from_model": "giscedata.lectures.comptador",
            "active_ids": [mtr_id],
            "active_id": mtr_id,
        }
        wiz_id = wiz_measures_curve_o.create(cursor, uid, vals, context=ctx)
        try:
            wiz_measures_curve_o.load_measures(cursor, uid, [wiz_id], context=ctx)
        except Exception as e:
            if isinstance(e, osv.orm.except_orm):
                return False, "sense_corbes"
            else:
                return False, "error"

        wiz_measures_curve_o.create_measures(cursor, uid, [wiz_id], context=ctx)
        return True, "ok"

    def crear_lectura_calculada(self, cursor, uid, _id, context=None):
        def add_days(the_date, d):
            return (datetime.strptime(the_date, "%Y-%m-%d") + timedelta(days=d)).strftime(
                "%Y-%m-%d"
            )

        def today_str():
            return datetime.today().strftime("%Y-%m-%d")

        imd_o = self.pool.get("ir.model.data")
        lc_origin = imd_o.get_object_reference(
            cursor, uid, "som_facturacio_calculada", "origen_lect_calculada"
        )[1]
        mtr_o = self.pool.get("giscedata.lectures.comptador")

        pol_data = self.read(
            cursor, uid, _id, ["name", "data_ultima_lectura", "data_ultima_lectura_f1"]
        )
        pol_name = pol_data["name"]
        data_ultima_lect = pol_data["data_ultima_lectura"]
        data_ultima_lectura_f1 = pol_data["data_ultima_lectura_f1"]

        crear_lectures, text = self._check_conditions_polissa_calculades(
            cursor, uid, _id, context=context
        )
        if not crear_lectures:
            return _(u"La pòlissa {} no compleix les condicions perquè {}".format(pol_name, text))

        if data_ultima_lect and data_ultima_lect < data_ultima_lectura_f1:
            self.retrocedir_lot(cursor, uid, _id, context)
            return _(
                u"La pòlissa {} té lectura F1 amb data {} i data última factura {}.".format(
                    pol_name, data_ultima_lectura_f1, data_ultima_lect
                )
            )

        crear_lectures, text = self._check_conditions_lectures_calculades(
            cursor, uid, _id, context=context
        )
        if not crear_lectures:
            return _(u"La pòlissa {} {}".format(pol_name, text))

        mtr_id = mtr_o.search(cursor, uid, [("polissa.id", "=", _id), ("active", "=", True)])[0]
        start_date = add_days(data_ultima_lect, 1)
        data_seguent_lect_7 = add_days(data_ultima_lect, 7)
        data_seguent_lect_14 = add_days(data_ultima_lect, 14)
        data_seguent_lect_21 = add_days(data_ultima_lect, 21)

        datetime.today().strftime("%Y-%m-%d")

        for _date in [data_seguent_lect_21, data_seguent_lect_14, data_seguent_lect_7]:
            if _date > today_str() or _date > add_days(data_ultima_lectura_f1, 21):
                continue
            lect_created, msg = self.crear_lectura_data(
                cursor, uid, _id, _date, start_date, mtr_id, lc_origin, context
            )
            if lect_created:
                self.retrocedir_lot(cursor, uid, [_id], context=context)
                return _(u"La polissa {} té lectures creades en data {}".format(pol_name, _date))
            elif msg == "error" and context.get("raise_error", True):
                raise osv.except_osv(
                    _("Error"),
                    _(
                        u"La pòlissa {} no pot generar lectures per error inesperat de wizard {}.".format(  # noqa: E501
                            pol_name, str(e)  # noqa: F821
                        )
                    ),
                )
            elif msg == "error":
                return _(
                    u"La pòlissa {} no pot generar lectures per error inesperat de wizard {}.".format(  # noqa: E501
                        pol_name, str(e)  # noqa: F821
                    )
                )

        return _(u"La pòlissa {} no pot generar lectures per falta de corba.".format(pol_name))

    def crear_lectures_calculades(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        context["raise_error"] = False

        msgs = []
        for _id in ids:
            result = self.crear_lectura_calculada(cursor, uid, _id, context)
            msgs.append(result)

        return msgs

    @job(queue="facturacio_calculada")
    def crear_lectura_calculades_async(self, cursor, uid, pol_id, context=None):
        return self.crear_lectura_calculada(cursor, uid, pol_id, context=None)

    _columns = {}

    _defaults = {}


GiscedataPolissaCalculada()
