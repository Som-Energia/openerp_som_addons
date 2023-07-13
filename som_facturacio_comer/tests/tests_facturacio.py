# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
from datetime import datetime
from dateutil.relativedelta import relativedelta
import netsvc


class TestsGiscedataFacturacioDeute(testing.OOTestCase):

    def get_object_reference_browse(self, cursor, uid, module, reference):
        model, oid = self.openerp.pool.get("ir.model.data").get_object_reference(cursor, uid, module, reference)
        return self.openerp.pool.get(model).browse(cursor, uid, oid)

    def test_mesos_antiguitat_factura_impagada_mes_antiga_de_contracte(self):
        '''
        -Agafem contracte demo
        -Creem factura
        -Creem proces impagament
        -Llegim el camp mesos_factura_mes_antiga_impagada de la polissa i validem
        que te valor 0 ja que no hi ha cap factura impagada
        -Obrim la factura i la marquem com a impagada
        -Llegim el camp mesos_factura_mes_antiga_impagada de la polissa i validem
        que te valor 0 ja que la factura te el date_invoice a dia avui
        -Canviem el date_invoice de la factura per 2 mesos enrere
        -Llegim el camp mesos_factura_mes_antiga_impagada de la polissa i validem
        que te valor 2 ja que la factura te el date_invoice a 2 mesos enrere
        '''
        self.openerp.install_module('giscedata_tarifas_pagos_capacidad_20210601')
        self.openerp.install_module('giscedata_tarifas_peajes_20210601')
        self.openerp.install_module('giscedata_tarifas_cargos_20210601')
        imd_obj = self.openerp.pool.get('ir.model.data')
        contract_obj = self.openerp.pool.get('giscedata.polissa')
        fact_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        lot_obj = self.openerp.pool.get('giscedata.facturacio.lot')
        clot_obj = self.openerp.pool.get('giscedata.facturacio.contracte_lot')
        pstate_obj = self.openerp.pool.get('account.invoice.pending.state')
        payment_mode_obj = self.openerp.pool.get('payment.mode')
        conf_obj = self.openerp.pool.get('res.config')

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            contract_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_polissa', 'polissa_tarifa_018')[1]
            conf_obj.set(cursor, uid, "allow_negative_consume", 1)

            # Configurem algunes variables
            conf_obj.set(cursor, uid, "inici_final_use_lot", 0)
            # Evitem que crei cas B1 al posar pending perque demana moltes dades
            conf_obj.set(cursor, uid, 'atr_b1_from_pending_state', 0)
            # Creem lots de facturacio
            lot_obj.crear_lots_mensuals(cursor, uid, 2021)
            lot_id = lot_obj.search(cursor, uid, [('name', '=', '06/2021')], limit=1)[0]

            contracte = contract_obj.read(cursor, uid, contract_id, ['payment_mode_id'])

            payment_mode_id = contracte['payment_mode_id'][0]
            payment_mode_obj.write(cursor, uid, [payment_mode_id], {"name": "ENGINYERS"})

            # Activem el contracte. Les dades que te de demo ja son correctes (si, increible). Fins i tot les lectures
            contract_obj.write(cursor, uid, contract_id, {'lot_facturacio': lot_id})
            contract_obj.send_signal(cursor, uid, [contract_id], ['validar', 'contracte'])

            # Intentem valida i facturar a traves del lot de facturacio per facturar el mes 05
            # Validacio
            contracte_lot_id = clot_obj.search(cursor, uid, [('polissa_id', '=', contract_id), ('lot_id', '=', lot_id)])
            self.assertEqual(len(contracte_lot_id), 1)
            contracte_lot_id = contracte_lot_id[0]
            clot_obj.write(cursor, uid, contracte_lot_id, {'state': 'obert'})
            lot_obj.write(cursor, uid, lot_id, {'state': 'obert'})
            with PatchNewCursors():
                clot_obj.wkf_obert(cursor, uid, [contracte_lot_id], {'from_lot': False})
            clot_info = clot_obj.read(cursor, uid, contracte_lot_id, [])
            self.assertEqual(clot_info['state'], "facturar")
            self.assertFalse(clot_info['status'])

            # Facturacio
            with PatchNewCursors():
                clot_obj.facturar(cursor, uid, [contracte_lot_id])
            clot_info = clot_obj.read(cursor, uid, contracte_lot_id, [])
            self.assertEqual(clot_info['state'], "facturat")
            self.assertFalse(clot_info['status'])

            # Comprovem la factura creada
            factura_id = fact_obj.search(cursor, uid, [('lot_facturacio', '=', lot_id)])
            invoice = fact_obj.browse(cursor, uid, factura_id)[0]
            #proces de tall que te la polissa per defecte
            default_process_id = imd_obj.get_object_reference(
                cursor, uid, 'account_invoice_pending',
                'default_pending_state_process'
            )[1]
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(
                uid, 'account.invoice', invoice.invoice_id.id, 'invoice_open', cursor
            )
            #creem un estat per a poder fer impagament despres
            id_10 = pstate_obj.create(cursor, uid, {
                'name': 'Weight 10',
                'weight': 1,
                'process_id': default_process_id
            })
            contracte = contract_obj.read(cursor, uid, contract_id, ['mesos_factura_mes_antiga_impagada'])
            mesos_factura_impagada = contracte['mesos_factura_mes_antiga_impagada']
            # Com no hi ha cap factura impagada posem 0
            self.assertEqual(mesos_factura_impagada, 0)
            invoice.set_pending(id_10)

            contracte = contract_obj.read(cursor, uid, contract_id, ['mesos_factura_mes_antiga_impagada'])
            mesos_factura_impagada = contracte['mesos_factura_mes_antiga_impagada']
            # Com la factura te el date_invoice a dia d'avui ens ensenyara 0 mesos
            self.assertEqual(mesos_factura_impagada, 0)

            #canviem el date invoice per 2 mesos enrere. Al canviar la data s'executara el trigger i
            #es tornara a calcular el camp mesos_factura_mes_antiga_impagada
            data_enrere = datetime.today() - relativedelta(months=2)
            invoice.write({'date_invoice': data_enrere})
            contracte = contract_obj.read(cursor, uid, contract_id, ['mesos_factura_mes_antiga_impagada'])
            mesos_factura_impagada = contracte['mesos_factura_mes_antiga_impagada']
            #Com la factura te el date_invoice a 2 mesos enrere ens ensenyara 2 mesos
            self.assertGreater(mesos_factura_impagada, 0)
            self.assertEqual(mesos_factura_impagada, 2)
