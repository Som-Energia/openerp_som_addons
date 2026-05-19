# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import date, timedelta
import os


def today_str():
    return date.today().strftime("%Y-%m-%d")


def today_minus_str(d):
    return (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")


class SomAutoreclamaBaseTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.old_oorq_async = os.environ.get('OORQ_ASYNC')
        os.environ['OORQ_ASYNC'] = 'True'

    def tearDown(self):
        self.txn.stop()
        if self.old_oorq_async:
            os.environ['OORQ_ASYNC'] = self.old_oorq_async

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def search_in(self, model, params):
        model_obj = self.get_model(model)
        found_ids = model_obj.search(self.cursor, self.uid, params)
        return found_ids[0] if found_ids else None

    def browse_referenced(self, reference):
        model, id = reference.split(",")
        model_obj = self.get_model(model)
        return model_obj.browse(self.cursor, self.uid, int(id))

    def get_object_reference(self, module, semantic_id):
        ir_obj = self.get_model("ir.model.data")
        expected_id = ir_obj.get_object_reference(
            self.cursor, self.uid, module, semantic_id
        )
        return expected_id

    def create_tags(self):
        tag_obj = self.get_model("giscedata.atc.tag")
        tag_obj.create(self.cursor, self.uid, {
            'name': "[GET] Expedient FRAU",
            'description': "Bla bla bla",
        })
        tag_obj.create(self.cursor, self.uid, {
            'name': "[GET] Expedient ANOMALIA",
            'description': "Bla bla bla",
        })

    def build_atc(
        self,
        subtype="029",
        r1=False,
        channel="intercambi",
        section="client",
        log_days=3,
        agent_actual="10",
        state="pending",
        active=True,
        date_closed=None,
        date=None,
        polissa="polissa_0002",
    ):
        atc_obj = self.get_model("giscedata.atc")
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", polissa
        )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", channel)])
        section_id = self.search_in("crm.case.section", [("name", "ilike", section)])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", subtype)])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": r1,
            "crear_cas_r1": r1,
        }
        atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )
        last_write = {
            "agent_actual": agent_actual,
            "state": state,
            "active": active,
        }
        if date:
            last_write['date'] = date
        atc_obj.write(
            self.cursor,
            self.uid,
            atc_id,
            last_write,
        )
        if date_closed:
            atc_obj.write(
                self.cursor,
                self.uid,
                atc_id,
                {'date_closed': date_closed}
            )
        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        log_obj = self.get_model("crm.case.log")
        log_obj.write(self.cursor, self.uid, atc.log_ids[1].id, {"date": today_minus_str(log_days)})

        return atc_id

    def build_polissa(
        self,
        name="polissa_0002",
        f1_date_days_from_today=None,
        initial_state=None,
        data_baixa=None,
        data_baixa_from_today=None,
        pool_readings=None
    ):
        f1i_obj = self.get_model("giscedata.polissa.f1.info")
        h_obj = self.get_model("som.autoreclama.state.history.polissa")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", name
        )

        if f1_date_days_from_today is not None:
            date = today_minus_str(f1_date_days_from_today)
            f1i_obj.create(
                self.cursor,
                self.uid,
                {
                    'polissa_id': polissa_id,
                    'data_ultima_lectura_f1': date,
                }
            )

        states = {
            'correct': "correct_state_workflow_polissa",
            'loop': "loop_state_workflow_polissa",
            'disabled': "disabled_state_workflow_polissa",
        }
        if initial_state in states:
            _, st_id = self.get_object_reference(
                "som_autoreclama",
                states[initial_state]
            )
            h_obj.historize(
                self.cursor, self.uid,
                polissa_id,
                st_id,
                None,
                None
            )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        pol_obj = self.get_model("giscedata.polissa")
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        if data_baixa_from_today:
            data_baixa = today_minus_str(data_baixa_from_today)

        if data_baixa is not None:
            vals = {"data_baixa": data_baixa}
            if data_baixa:
                vals['state'] = 'baixa'

            pol_obj.write(self.cursor, self.uid, polissa_id, vals)

        if pool_readings:
            meter_obj = self.get_model("giscedata.lectures.comptador")
            meter_id = meter_obj.create(self.cursor, self.uid, {
                'polissa': polissa_id,
                'name': 'Comptador prova',
                'data_alta': '1977-08-26',
            })
            pl_obj = self.get_model("giscedata.lectures.lectura.pool")
            for pool_reading in pool_readings:
                pl_obj.create(self.cursor, self.uid, {
                    'comptador': meter_id,
                    'name': self.get_lectura_date(pool_reading),
                    'lectura': self.get_lectura(pool_reading),
                    'origen_id': self.get_origen_id(pool_reading),
                    'periode': self.get_periode_id(pool_reading),
                    'tipus': 'A',
                })

        return polissa_id

    def get_lectura_date(self, pool_reading):
        if 'date' in pool_reading:
            return pool_reading['date']

        if 'days_ago' in pool_reading:
            return today_minus_str(pool_reading['days_ago'])

        return today_str()

    def get_lectura(self, pool_reading):
        return pool_reading.get('lectura', 1000)

    def get_origen_id(self, pool_reading):
        origen = pool_reading.get('origen', '10')
        if origen == 'real':
            origen = '10'
        elif origen in ['est', 'estimada']:
            origen = '40'

        return self.search_in("giscedata.lectures.origen", [("codi", "=", origen)])

    def get_periode_id(self, pool_reading):
        periode = pool_reading.get('periode', 'P1')
        return self.search_in("giscedata.polissa.tarifa.periodes", [("name", "=", periode)])

    def add_done_006_to_polissa(self, pol_id, days):
        dat = today_minus_str(days)
        return self.build_atc(subtype="006", state='done', date_closed=dat, date=dat, r1=False)

    def add_done_009_to_polissa(self, pol_id, days):
        dat = today_minus_str(days)
        return self.build_atc(subtype="009", state='done', date_closed=dat, date=dat, r1=False)

    def add_to_history_base(self, pol_id, days, atc_id, model_name, state_semantic_id):
        imd_obj = self.get_model("ir.model.data")
        polh_obj = self.get_model(model_name)
        correct_state_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_autoreclama", state_semantic_id
        )[1]
        polh_obj.historize(
            self.cursor, self.uid, pol_id, correct_state_id, today_minus_str(days), atc_id)

    def add_correct_to_history(self, pol_id, days, atc_id=None):
        self.add_to_history_base(pol_id, days, atc_id,
                                 "som.autoreclama.state.history.polissa",
                                 "correct_state_workflow_polissa")

    def add_correct_to_history009(self, pol_id, days, atc_id=None):
        self.add_to_history_base(pol_id, days, atc_id,
                                 "som.autoreclama.state.history.polissa009",
                                 "correct_state_workflow_polissa009")

    def add_review_to_history(self, pol_id, days, atc_id=None):
        self.add_to_history_base(pol_id, days, atc_id,
                                 "som.autoreclama.state.history.polissa",
                                 "review_state_workflow_polissa")

    def add_review_to_history009(self, pol_id, days, atc_id=None):
        self.add_to_history_base(pol_id, days, atc_id,
                                 "som.autoreclama.state.history.polissa009",
                                 "review_state_workflow_polissa009")

    def get_number_of_db_connections(self):
        sql = "SELECT count(*) FROM pg_stat_activity;"
        self.cursor.execute(sql)
        vals = self.cursor.fetchall()
        return vals[0][0]

    def get_db_connections_list(self):
        fields = ['pid', 'datid', 'datname', 'usename', 'application_name', 'wait_event_type',
                  'wait_event', 'state', 'query', 'backend_type']
        sql = "SELECT {} FROM pg_stat_activity;".format(", ".join(fields))
        self.cursor.execute(sql)
        vals = self.cursor.fetchall()
        res = []
        for val in vals:
            res.append(dict(zip(fields, val)))
        return res
