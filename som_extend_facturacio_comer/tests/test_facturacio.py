# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
from datetime import timedelta, datetime


def crear_modcon(pool, cursor, uid, polissa_id, values, ini, fi):
    polissa_obj = pool.get("giscedata.polissa")
    pol = polissa_obj.browse(cursor, uid, polissa_id)
    pol.send_signal(["modcontractual"])
    polissa_obj.write(cursor, uid, polissa_id, values)
    if "potencia" in values:
        pol.generar_periodes_potencia(context={"force_genpot": True})
    wz_crear_mc_obj = pool.get("giscedata.polissa.crear.contracte")

    ctx = {"active_id": polissa_id}
    params = {"duracio": "nou"}

    wz_id_mod = wz_crear_mc_obj.create(cursor, uid, params, ctx)
    wiz_mod = wz_crear_mc_obj.browse(cursor, uid, wz_id_mod, ctx)
    wz_crear_mc_obj.onchange_duracio(
        cursor, uid, [wz_id_mod], wiz_mod.data_inici, wiz_mod.duracio, ctx
    )
    wiz_mod.write({"data_inici": ini, "data_final": fi})
    wiz_mod.action_crear_contracte(ctx)


class TestsFacturacioValidation(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

    def tearDown(self):
        self.txn.stop()

    def test_check_missing_days(self):
        """
        Obtenir dues factures f1, f2
        Obtenir un lot de facturacio
        Assignar les f1, f2 al lot
        Modificar la f1 i fer-la curta
        Verificar que no salta l'alerta
        Obtenir una modcon
        Assignar la modcon a la factura
        Modificar la modcon perque tingui data d'inici l'andemà del final de la factura
        Modificar totes les factures futures i posar-les al passat
        Verificar que salta l'alerta
        Modificar la factura f2 perque sigui posterior a f1
        Verificar que no salta l'alerta
        """
        cursor = self.txn.cursor
        uid = self.txn.user
        imd_obj = self.openerp.pool.get("ir.model.data")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        validator_obj = self.openerp.pool.get("giscedata.facturacio.validation.validator")
        self.openerp.pool.get("giscedata.polissa")
        f1_id = imd_obj.get_object_reference(cursor, uid, "giscedata_facturacio", "factura_0006")[1]
        f2_id = imd_obj.get_object_reference(cursor, uid, "giscedata_facturacio", "factura_0007")[1]

        factures = [f1_id, f2_id]

        lot_id = imd_obj.get_object_reference(cursor, uid, "giscedata_facturacio", "lot_0002")[1]

        fact_obj.write(cursor, uid, factures, {"lot_facturacio": lot_id})
        data_inici = fact_obj.read(cursor, uid, factures[0], ["data_inici"])["data_inici"]
        start_date = datetime.strptime(data_inici, "%Y-%m-%d")
        end_date = start_date + timedelta(days=2)
        fact_obj.write(
            cursor,
            uid,
            factures[0],
            {"lot_facturacio": lot_id, "data_final": start_date + timedelta(days=2)},
        )

        parameters = {"n_days_mensual": 5, "n_days_bimensual": 10, "n_days_anual": 1}

        fact = fact_obj.browse(cursor, uid, factures[0])
        res = validator_obj.check_missing_days(cursor, uid, fact, parameters)
        self.assertIsNone(res)

        modcon_inici = end_date + timedelta(days=1)
        facts = fact_obj.search(
            cursor, uid, [("polissa_id", "=", fact.polissa_id.id), ("id", "!=", factures[0])]
        )

        fact_obj.write(
            cursor,
            uid,
            facts,
            {"data_inici": "1000-01-01", "data_final": "1000-02-02"},
            context={"skip_cnt_llista_preu_compatible": True},
        )

        fact.polissa_id.send_signal(["validar", "contracte"])

        crear_modcon(
            self.openerp.pool,
            cursor,
            uid,
            fact.polissa_id.id,
            {},
            modcon_inici.strftime("%Y-%m-%d"),
            modcon_inici.strftime("%Y-%m-%d"),
        )

        res = validator_obj.check_missing_days(cursor, uid, fact, parameters)
        self.assertIsNotNone(res)

        fact_obj.write(
            cursor,
            uid,
            factures[1],
            {"data_inici": "9300-01-01", "data_final": "9300-02-02"},
            context={"skip_cnt_llista_preu_compatible": True},
        )

        res = validator_obj.check_missing_days(cursor, uid, fact, parameters)
        self.assertIsNone(res)
