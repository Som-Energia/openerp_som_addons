# -*- encoding: utf-8 -*-
import netsvc
from osv import osv, fields
from datetime import datetime, timedelta
from tools.translate import _


class WizardRefundRectifyFromOrigin(osv.osv_memory):

    _name = 'wizard.refund.rectify.from.origin'


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

        lect_obj.unlink(cursor, uid, lects_esborrar)

        lects_pot_esborrar = lect_pot_obj.search(cursor, uid, search_params, context={'active_test':False})
        if lects_pot_esborrar:
            lect_pot_obj.unlink(cursor, uid, lects_pot_esborrar)

        ####### carrega lectures de l'F1 afectat ######
        pol_obj.write(cursor, uid, pol_id, {'data_ultima_lectura': data_lectura_anterior})

        wiz_id = carrega_lect_wiz_o.create(cursor, uid, {'date': data_final_rectificacio}, context={'model':'giscedata.polissa'})
        carrega_lect_wiz_o.action_carrega_lectures(cursor, uid, [wiz_id], context={'active_id': pol_id,'active_ids':[pol_id],'model':'giscedata.polissa'})
        pol_obj.write(cursor, uid, pol_id, {'data_ultima_lectura': data_ultima_lectura})

        return len(lects_esborrar)

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

        agrupar_ctx = {'active_id':fres_resultat[0], 'active_ids':fres_resultat, 'model':'giscedata.facturacio.factura'}
        wiz_id = wiz_ag_o.create(cursor, uid, {}, context=agrupar_ctx)
        wiz = wiz_ag_o.browse(cursor, uid, wiz_id)
        if wiz.amount_total == 0:
            return False, "L'agrupació de factures fan un total de 0. S'atura el procés."

        elif wiz.amount_total < 0:
            total_import = wiz.amount_total
            res = wiz_ag_o.agrupar_remesar(cursor, uid, [wiz.id], context=agrupar_ctx)
            remesar_ctx = res['context']
            wiz_remesar_o = self.pool.get(res['res_model'])
            wiz_remesa_id = wiz_remesar_o.create(cursor, uid, {'tipus': 'payable', 'order': payment_order_id}, context=remesar_ctx)
            wiz_remesar_o.action_afegir_factures(wiz_remesa_id, context=remesar_ctx)
            return True, "S'han agrupat les factures i s'han remesat, ja que l'import agrupat és {}".format(total_import)
        else:
            wiz_ag_o.group_invoices(cursor, uid, [wiz.id], context=agrupar_ctx)
            return True, "S'han agrupat les factures, l'import agrupat és {}".format(total_import)


    def refund_rectify_by_origin(self, cursor, uid, ids, context={}):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz = self.browse(cursor, uid, ids[0])
        if wiz.send_mail and not wiz.email_template:
            raise osv.except_osv(_('Error'), _('Per enviar el correu cal indicar una plantilla'))

        if wiz.open_invoices and not wiz.order:
            raise osv.except_osv(_('Error'), _('Per remesar les factures a pagar cal una ordre de pagament'))

        active_ids = context.get('active_ids', [])
        msg = []
        facts_over_amount = []

        for _id in active_ids:
            try:
                fact_prov = fact_obj.browse(cursor, uid, _id)
                origen = fact_prov.origin
                pol_id = fact_prov.polissa_id.id
                pol_name = fact_prov.polissa_id.name
                if fact_prov.polissa_id.facturacio_suspesa:
                    msg.append('La pòlissa {}, que té la factura amb origen {}, té facturació suspesa. No s\'actua.'.format(pol_name, origen))
                    continue
                if fact_prov.type != 'in_invoice':
                    msg.append('La factura amb origen {} no es de tipus in_invoice, no s\'actua'.format(origen))
                    continue
                facts_cli_ids, msg_get = self.get_factures_client_by_dates(cursor, uid, ids, pol_id, fact_prov.data_inici, fact_prov.data_final, context)
                if msg_get:
                    msg.append("Pòlissa {} per factura amb origen {}: {}".format(pol_name, origen, msg_get))
                if not facts_cli_ids:
                    msg.append('La factura amb origen {} no té res per abonar i rectificar, no s\'actua'.format(origen))
                    continue

                n_lect_del = self.recarregar_lectures_between_dates(cursor, uid, ids, pol_id, fact_prov.data_inici, fact_prov.data_final, context)
                if not n_lect_del:
                    msg.append("La pòlissa {}, que té la factura amb origen {}, no té lectures per esborrar. No s'hi actua.".format(pol_name, origen))
                    continue

                msg.append("S'han esborrat {} lectures de la pòlissa {}".format(n_lect_del, pol_name))
                facts_created, msg_rr = self.refund_rectify_if_needed(cursor, uid, ids, facts_cli_ids, context)
                msg += msg_rr
                if wiz.max_amount:
                    facts_over_limit = self.check_max_amount(cursor, uid, ids, facts_created, wiz.max_amount, context)
                    if facts_over_limit:
                        facts_over_amount += facts_created
                        msg.append("La pòlissa {} té alguna factura d'import superior al límit, cal revisar les factures. No continua el procés.". format(pol_name))
                        continue
                self.write(cursor, uid, ids, {'facts_generades': [(4,_id) for _id in facts_created]})
                if wiz.open_invoices:
                    self.open_group_invoices(cursor, uid, ids, facts_created, wiz.order.id, context)
                if wiz.send_mail:
                    self.send_polissa_mail(cursor, uid, ids, pol_id, context)
            except Exception as e:
                msg.append("Error processant la factura amb origen {}: {}".format(origen, str(e)))
        self.write(cursor, uid, ids, {'info': '\n'.join(msg), 'state': 'end'})


    _columns = {
        'state': fields.selection(
            [('init', 'Initial'), ('end', 'End')], 'State'
        ),
        'order': fields.many2one('payment.order', 'Remesa'),
        'open_invoices': fields.boolean(_("Obrir, agrupar i remesar (si són a pagar) les factures")),
        'send_mail': fields.boolean(_("Enviar el correu de pòlissa")),
        'info': fields.text(_('Informació'), readonly=True),
        'facts_generades': fields.many2many(
            'giscedata.facturacio.factura', 'sw_wiz_rrfo',
            'wiz_fact_id', 'fact_id', string='Factures generades',
            readonly=True
        ),
        'max_amount': fields.float("Import màxim"),
        'email_template': fields.many2one(
            'poweremail.templates', 'Plantilla del correu',
            domain="[('object_name.model', '=', 'giscedata.polissa')]"
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }

WizardRefundRectifyFromOrigin()
