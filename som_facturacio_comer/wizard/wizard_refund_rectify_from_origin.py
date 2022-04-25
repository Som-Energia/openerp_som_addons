# -*- encoding: utf-8 -*-
import netsvc, pooler
from oorq.oorq import AsyncMode
from osv import osv, fields
from datetime import datetime, timedelta
import json, csv, base64
from StringIO import StringIO
from tools.translate import _


class WizardRefundRectifyFromOrigin(osv.osv_memory):

    _name = 'wizard.refund.rectify.from.origin'


    def send_polissa_mail(self, cursor, uid, ids, pol_id, plantilla, context):
        pem_send_wo = self.pool.get('poweremail.send.wizard')
        ctx = {
            'active_ids': [pol_id],
            'active_id': pol_id,
            'template_id': plantilla.id,
            'src_model': 'giscedata.polissa',
            'src_rec_ids': [pol_id],
            'from': plantilla.enforce_from_account.id,
            'state': 'single',
            'priority': 0,
        }
        params = {
            'state': 'single',
            'priority': 0,
            'from': plantilla.enforce_from_account.id,
        }

        wz_id = pem_send_wo.create(cursor, uid, params, ctx)
        result = pem_send_wo.send_mail(cursor, uid, [wz_id], ctx)

    def get_factures_client_by_dates(self, cursor, uid, ids, pol_id, data_inici, data_final, context={}):
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        msg = ''
        facts_cli_ids = fact_obj.search(cursor, uid, [
            ('polissa_id', '=', pol_id), ('type','=', 'out_invoice'),
            ('refund_by_id', '=', False), ('data_inici','<', data_final),
            ('data_final','>', data_inici)
            ], order='data_inici asc')

        f_cli_rectificar_draft = fact_obj.search(cursor, uid, [
            ('id', 'in', facts_cli_ids), ('state','=','draft')
        ])
        if f_cli_rectificar_draft:
            fact_obj.unlink(cursor, uid, f_cli_rectificar_draft)
            msg = "S'han eliminat {} factures en esborrany".format(len(f_cli_rectificar_draft))
            facts_cli_ids = list(set(facts_cli_ids) - set(f_cli_rectificar_draft))
        return facts_cli_ids, msg

    def recarregar_lectures_between_dates(self, cursor, uid, ids, pol_id, data_inici, data_final, context={}):
        pol_obj = self.pool.get('giscedata.polissa')
        lect_obj = self.pool.get('giscedata.lectures.lectura')
        lect_pot_obj = self.pool.get('giscedata.lectures.potencia')
        carrega_lect_wiz_o = self.pool.get('giscedata.lectures.pool.wizard')

        polissa = pol_obj.browse(cursor, uid, pol_id)
        data_ultima_lectura = polissa.data_ultima_lectura

        data_lectura_anterior = (datetime.strptime(data_inici, '%Y-%m-%d') - timedelta(days=1)).strftime("%Y-%m-%d")
        data_final_rectificacio = data_final
        comptadors_actius = polissa.comptadors_actius(data_lectura_anterior, data_final)

        if not isinstance(comptadors_actius, (list, tuple)):
            comptadors_actius= [comptadors_actius]

        search_params = [
            ('name','>=', data_lectura_anterior),
            ('name','<=',data_final),
            ('comptador', 'in', comptadors_actius),
        ]

        lects_esborrar = lect_obj.search(cursor, uid, search_params, context={'active_test':False})
        if not lects_esborrar:
            return False

        db = pooler.get_db_only(cursor.dbname)
        nou_cr = db.cursor()
        lect_obj.unlink(nou_cr, uid, lects_esborrar)

        lects_pot_esborrar = lect_pot_obj.search(nou_cr, uid, search_params, context={'active_test':False})
        if lects_pot_esborrar:
            lect_pot_obj.unlink(nou_cr, uid, lects_pot_esborrar)
        nou_cr.commit()
        ####### carrega lectures de l'F1 afectat ######
        self.carrega_lectures(cursor, uid, ids, data_final_rectificacio, data_lectura_anterior, comptadors_actius, context)
        return len(lects_esborrar)

    def carrega_lectures(self, cursor, uid, ids, data_final_rectificacio, data_lectura_anterior, comptador_ids,  context):
        comptador_obj = self.pool.get('giscedata.lectures.comptador')
        with AsyncMode('sync') as asmode:
            # Carreguem lectures de pool del comptador a facturació del periode
            # que cal rectificar
            ctx = context.copy()
            ctx.update({
                'allow_new_measures': False,
                'data_ultima_lectura': data_lectura_anterior,
            })
            carrega_lectures = comptador_obj.get_lectures_from_pool(
                cursor, uid, comptador_ids, data_final_rectificacio, context=ctx
            )
        return True


    def refund_rectify_if_needed(self, cursor, uid, ids, f_ids, context={}):
        wiz_ranas_o = self.pool.get('wizard.ranas')
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        ctx={'active_ids':f_ids, 'active_id':f_ids[0]}
        wiz_id = wiz_ranas_o.create(cursor, uid, {}, context=ctx)
        fres_resultat = wiz_ranas_o.action_rectificar(cursor, uid, wiz_id, context=ctx)
        msg = []

        f_res_info = fact_obj.read(cursor, uid, fres_resultat, ['rectifying_id','amount_total','invoice_id'])

        #Eliminem les que no cal rectificar (import AB == import RE)
        for initial_id in f_ids:
            inv_id = fact_obj.read(cursor, uid, initial_id, ['invoice_id'])['invoice_id'][0]
            rectifying_amounts = filter(lambda x: x['rectifying_id'][0] == inv_id, f_res_info)
            if len(set([x['amount_total'] for x in rectifying_amounts])) == 1:
                ab_re_ids = [x['id'] for x in rectifying_amounts]
                fact_obj.unlink(cursor, uid, ab_re_ids)
                msg.append("Per la factura origen {} les factures AB i RE tenen mateix import, s'esborren")
                fres_resultat = list(set(fres_resultat) - set(ab_re_ids))

        return fres_resultat, msg

    def check_max_amount(self, cursor, uid, ids, facts_ids, max_amount, context):
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for _id in facts_ids:
            factura = fact_obj.browse(cursor, uid, _id)
            if factura.type == 'out_refund':
                continue
            if factura.amount_total > max_amount:
                return True

    def open_group_invoices(self, cursor, uid, ids, facts_created, payment_order_id, context={}):

        wiz_ag_o = self.pool.get('wizard.group.invoices.payment')
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        db = pooler.get_db_only(cursor.dbname)
        tmp_cr = db.cursor()
        try:
            fact_infos = fact_obj.read(cursor, uid, facts_created, ['id', 'date_invoice'])
            sorted_factures = sorted(
                fact_infos, key=lambda f: f['date_invoice']
            )
            for factura in sorted_factures:
                factura_id = factura['id']
                fact_obj.invoice_open(cursor, uid, [factura_id], context=context)

            tmp_cr.commit()
        except Exception as exc:
            tmp_cr.rollback()
            return False, "Error en obrir les factures, no continua el procés"
        finally:
            tmp_cr.close()

        agrupar_ctx = {'active_id':facts_created[0], 'active_ids':facts_created, 'model':'giscedata.facturacio.factura'}
        wiz_id = wiz_ag_o.create(cursor, uid, {}, context=agrupar_ctx)
        wiz = wiz_ag_o.browse(cursor, uid, wiz_id)
        total_import = wiz.amount_total
        if wiz.amount_total == 0:
            return False, "L'agrupació de factures fan un total de 0. S'atura el procés."

        elif total_import < 0:
            total_import = wiz.amount_total
            res = wiz_ag_o.agrupar_remesar(cursor, uid, [wiz.id], context=agrupar_ctx)
            remesar_ctx = res['context']
            wiz_remesar_o = self.pool.get(res['res_model'])
            wiz_remesa_id = wiz_remesar_o.create(cursor, uid, {'tipus': 'payable', 'order': payment_order_id}, context=remesar_ctx)
            wiz_remesar_o.action_afegir_factures(cursor, uid, wiz_remesa_id, context=remesar_ctx)
            return True, "S'han agrupat les factures i s'han remesat, ja que l'import agrupat és {}".format(total_import)
        else:
            wiz_ag_o.group_invoices(cursor, uid, [wiz.id], context=agrupar_ctx)
            return True, "S'han agrupat les factures, l'import agrupat és {}".format(total_import)

    def write_report(self, cursor, uid, ids, fact_csv_result, context):
        wizard = self.browse(cursor, uid, ids[0])
        csv_file = StringIO()
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow(['Origen', 'Pòlissa', 'Resultat'])
        writer.writerows(fact_csv_result)
        res_file = base64.b64encode(csv_file.getvalue())
        today = datetime.today().strftime('%Y%m%d')
        wizard.write({
            'report_file': res_file,
        })
        csv_file.close()

    def refund_rectify_by_origin(self, cursor, uid, ids, context={}):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz = self.browse(cursor, uid, ids[0])
        if wiz.send_mail and not wiz.email_template:
            raise osv.except_osv(_('Error'), _('Per enviar el correu cal indicar una plantilla'))
        if wiz.email_template and not wiz.email_template.enforce_from_account:
            raise osv.except_osv(_('Error'), _('La plantilla no té indicat el compte des del qual enviar'))
        if wiz.open_invoices and not wiz.order:
            raise osv.except_osv(_('Error'), _('Per remesar les factures a pagar cal una ordre de pagament'))

        active_ids = context.get('active_ids', [])
        msg = []
        facts_generades = []
        fact_csv_result = []
        for _id in active_ids:
            try:
                fact_prov = fact_obj.browse(cursor, uid, _id)
                origen = fact_prov.origin
                pol_id = fact_prov.polissa_id.id
                pol_name = fact_prov.polissa_id.name
                if fact_prov.polissa_id.facturacio_suspesa:
                    msg.append('La pòlissa {}, que té la factura amb origen {}, té facturació suspesa. No s\'actua.'.format(pol_name, origen))
                    fact_csv_result.append([origen, pol_name, "Pòlissa amb facturació suspesa"])
                    continue
                if fact_prov.type != 'in_invoice':
                    msg.append('La factura amb origen {} no es de tipus in_invoice, no s\'actua'.format(origen))
                    fact_csv_result.append([origen, pol_name, "La factura seleccionada no és de tipus Factura Proveïdor"])
                    continue
                facts_cli_ids, msg_get = self.get_factures_client_by_dates(cursor, uid, ids, pol_id, fact_prov.data_inici, fact_prov.data_final, context)
                if msg_get:
                    msg.append("Pòlissa {} per factura amb origen {}: {}".format(pol_name, origen, msg_get))
                if not facts_cli_ids:
                    msg.append('La factura amb origen {} no té res per abonar i rectificar, no s\'actua'.format(origen))
                    fact_csv_result.append([origen, pol_name, "No té res per abonar i rectificar, no s\'actua"])
                    continue

                n_lect_del = self.recarregar_lectures_between_dates(cursor, uid, ids, pol_id, fact_prov.data_inici, fact_prov.data_final, context)
                if not n_lect_del:
                    msg.append("La pòlissa {}, que té la factura amb origen {}, no té lectures per esborrar. No s'hi actua.".format(pol_name, origen))
                    fact_csv_result.append([origen, pol_name, "No té lectures per esborrar. No s'hi actua."])
                    continue

                facts_created, msg_rr = self.refund_rectify_if_needed(cursor, uid, ids, facts_cli_ids, context)
                msg.append("S'han esborrat {} lectures de la pòlissa {} i s'han generat {} factures".format(n_lect_del, pol_name, len(facts_created)))
                facts_generades += facts_created
                msg += msg_rr
                if wiz.max_amount:
                    facts_over_limit = self.check_max_amount(cursor, uid, ids, facts_created, wiz.max_amount, context)
                    if facts_over_limit:
                        msg.append("La pòlissa {} té alguna factura d'import superior al límit, cal revisar les factures. No continua el procés.". format(pol_name))
                        fact_csv_result.append([origen, pol_name, "Té alguna factura d'import superior al límit, cal revisar les factures. No continua el procés."])
                        continue
                if wiz.open_invoices:
                    self.open_group_invoices(cursor, uid, ids, facts_created, wiz.order.id, context)
                    msg.append("S'han obert les factures de la pòlissa {}.". format(pol_name))
                if wiz.send_mail:
                    self.send_polissa_mail(cursor, uid, ids, pol_id, wiz.email_template, context)
                    msg.append("S'ha enviat el correu a la pòlissa {}.". format(pol_name))
                fact_csv_result.append([origen, pol_name, "Ha arribat al final del procés (obrir factures: {}, enviar correu: {}).".format(
                    'Sí' if wiz.open_invoices else 'No', 'Sí' if wiz.send_mail else 'No')
                ])
            except Exception as e:
                msg.append("Error processant la factura amb origen {}: {}".format(origen, str(e)))
                fact_csv_result.append([origen, pol_name, "Hi ha hagut algun problema, cal revisar."])
        self.write_report(cursor, uid, ids, fact_csv_result, context)
        self.write(cursor, uid, ids, {'info': '\n'.join(msg), 'state': 'end', 'facts_generades': json.dumps(facts_generades)})

    def _show_invoices(self, cursor, uid, ids, context=None):
        fact_ids = self.read(cursor, uid, ids[0], ['facts_generades'])[0]['facts_generades']
        fact_ids = json.loads(fact_ids)
        return {
            'domain': "[('id','in', %s)]" % str(fact_ids),
            'name': 'Factures',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'giscedata.facturacio.factura',
            'type': 'ir.actions.act_window'
        }

    _columns = {
        'state': fields.selection(
            [('init', 'Initial'), ('end', 'End')], 'State'
        ),
        'order': fields.many2one('payment.order', 'Remesa'),
        'open_invoices': fields.boolean(_("Obrir, agrupar i remesar (si són a pagar) les factures")),
        'send_mail': fields.boolean(_("Enviar el correu de pòlissa")),
        'info': fields.text(_('Informació'), readonly=True),
        'facts_generades': fields.text(),
        'max_amount': fields.float("Import màxim",
            help="Import màxim a partir del qual les factures no s'obren i cal revisar. Si s'indica 0 no es comprova cap import"),
        'email_template': fields.many2one(
            'poweremail.templates', 'Plantilla del correu',
            domain="[('object_name.model', '=', 'giscedata.polissa')]"
        ),
        'report_file': fields.binary('Resultat', help="CSV amb el resultat"),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'max_amount': lambda *a: 2000,
    }

WizardRefundRectifyFromOrigin()
