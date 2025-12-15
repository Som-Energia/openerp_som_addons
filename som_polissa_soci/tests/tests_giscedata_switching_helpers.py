# -*- coding: utf-8 -*-
from __future__ import absolute_import

from giscedata_switching.tests.common_tests import TestSwitchingImport

from destral.transaction import Transaction
from destral.patch import PatchNewCursors
from addons import get_module_resource
import re
import mock


class TestC1(TestSwitchingImport):

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.subscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_load_c1_05(self, mock_subscribe):
        c102_xml_path = get_module_resource(
            'giscedata_switching', 'tests', 'fixtures', 'c102_new.xml')
        c105_xml_path = get_module_resource(
            'giscedata_switching', 'tests', 'fixtures', 'c105_new.xml')
        with open(c102_xml_path, 'r') as f:
            c102_xml = f.read()
        with open(c105_xml_path, 'r') as f:
            c105_xml = f.read()

        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            self.switch(txn, 'comer', other_id_name='res_partner_asus')

            # create step 01
            contract_id = self.get_contract_id(txn)
            step_id = self.create_case_and_step(
                cursor, uid, contract_id, 'C1', '01'
            )
            step_obj = self.openerp.pool.get('giscedata.switching.c1.01')
            sw_obj = self.openerp.pool.get('giscedata.switching')
            self.openerp.pool.get('giscedata.polissa')
            imd_obj = self.openerp.pool.get('ir.model.data')
            pp_obj = self.openerp.pool.get("product.pricelist")
            c101 = step_obj.browse(cursor, uid, step_id)
            c1 = sw_obj.browse(cursor, uid, c101.sw_id.id)
            codi_sollicitud = c1.codi_sollicitud
            CodigoREEEmpresaEmisora = '0002'
            codi_tarifa = '018'

            # change the codi sol.licitud of c102.xml
            c102_xml = c102_xml.replace(
                "<CodigoDeSolicitud>201607211259",
                "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
            )
            c102_xml = c102_xml.replace(
                "<CodigoREEEmpresaEmisora>1234",
                "<CodigoREEEmpresaEmisora>{0}".format(CodigoREEEmpresaEmisora)
            )
            c102_xml = c102_xml.replace(
                "<TarifaATR>003",
                "<TarifaATR>{0}".format(codi_tarifa)
            )

            # import step 02
            sw_obj.importar_xml(cursor, uid, c102_xml, 'c102.xml')

            # change the codi sol.licitud of c105.xml
            c105_xml = c105_xml.replace(
                "<CodigoDeSolicitud>201607211259",
                "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
            )
            c105_xml = c105_xml.replace(
                "<CodigoREEEmpresaEmisora>1234",
                "<CodigoREEEmpresaEmisora>{0}".format(CodigoREEEmpresaEmisora)
            )
            c105_xml = c105_xml.replace(
                "<TarifaATR>003",
                "<TarifaATR>{0}".format(codi_tarifa)
            )
            # remove <Autoconsumo> and everything inside (handles multi-line)
            c105_xml = re.sub(r'<Autoconsumo>.*?</Autoconsumo>', '', c105_xml, flags=re.DOTALL)

            # import step 05
            sw_obj.importar_xml(cursor, uid, c105_xml, 'c105.xml')

            res = sw_obj.search(cursor, uid, [
                ('proces_id.name', '=', 'C1'),
                ('step_id.name', '=', '05'),
                ('codi_sollicitud', '=', codi_sollicitud)
            ])
            self.assertEqual(len(res), 1)

            # Activar lot de facturació
            lot_obj = self.openerp.pool.get('giscedata.facturacio.lot')
            lot_ids = lot_obj.search(cursor, uid, [])
            lot_obj.write(cursor, uid, [lot_ids[0]], {
                'data_inici': '2016-10-01',
                'data_final': '2030-10-31',
                'name': '10/2030'
            })

            # Activar polissa
            self.pricelist_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio',
                'pricelist_tarifas_electricidad'
            )[1]
            pp_obj.write(cursor, uid, self.pricelist_id, {
                'type': 'sale',
            })

            c1 = sw_obj.browse(cursor, uid, res[0])
            with PatchNewCursors():
                sw_obj.activa_cas_atr(cursor, uid, c1)

            mock_subscribe.assert_called()
            self.assertEqual(c1.proces_id.name, 'C1')
            self.assertEqual(c1.step_id.name, '05')
            self.assertEqual(c1.partner_id.ref, '0002')
            self.assertEqual(c1.company_id.ref, '4321')
            self.assertEqual(c1.cups_id.name, 'ES1234000000000001JN0F')
            self.assertEqual(c1.cups_polissa_id.name, '0001C')
            c105 = sw_obj.get_pas(cursor, uid, c1)
            self.assertEqual(c105.data_activacio, '2016-08-21')
            self.assertEqual(c105.bono_social, '1')
            self.assertEqual(c105.tipus_contracte, '02')
            self.assertEqual(c105.tarifaATR, '018')
            self.assertEqual(c105.periodicitat_facturacio, '01')
            self.assertEqual(c105.control_potencia, '1')
            self.assertEqual(c105.contracte_atr, '00001')
            self.assertEqual(c105.tipus_telegestio, '01')
            self.assertEqual(c105.marca_medida_bt, 'S')
            self.assertEqual(c105.kvas_trafo, 0.05)
            self.assertEqual(c105.perdues, 5.0)
            self.assertEqual(c105.tensio_suministre, '10')
            self.assertEqual(len(c105.pot_ids), 2)
            self.assertEqual(c105.pot_ids[1].potencia, 2000)
            self.assertEqual(len(c105.pm_ids), 1)
            pm = c105.pm_ids[0]
            self.assertEqual(pm.tipus_moviment, 'A')
            self.assertEqual(pm.tipus, '03')
            self.assertEqual(pm.mode_lectura, '1')
            self.assertEqual(pm.funcio_pm, 'P')
            self.assertEqual(pm.tensio_pm, 0)
            self.assertEqual(pm.data, '2003-01-01')
            self.assertEqual(pm.data_alta, '2003-01-01')
            self.assertEqual(pm.data_baixa, '2003-02-01')
            self.assertEqual(len(pm.aparell_ids), 1)
            ap = pm.aparell_ids[0]
            self.assertEqual(ap.tipus, 'CG')
            self.assertEqual(ap.marca, '132')
            self.assertEqual(ap.tipus_em, 'L03')
            self.assertEqual(ap.propietari, 'Desc. Propietario')
            self.assertEqual(ap.periode_fabricacio, '2005')
            # self.assertEqual(ap.lectura_directa, 'N')
            self.assertEqual(ap.num_serie, '0000539522')
            self.assertEqual(ap.funcio, 'M')
            self.assertEqual(ap.constant_energia, 1)
            self.assertEqual(len(ap.mesura_ids), 2)
            mes = ap.mesura_ids[0]
            self.assertEqual(mes.tipus_dh, '6')
            self.assertEqual(mes.periode, '65')
            self.assertEqual(mes.magnitud, 'PM')
            self.assertEqual(mes.origen, '30')
            self.assertEqual(mes.lectura, 6.00)
            self.assertEqual(mes.data_lectura, '2003-01-02')
            self.assertEqual(mes.anomalia, '01')
            self.assertEqual(mes.text_anomalia, 'Comentario sobre anomalia')
