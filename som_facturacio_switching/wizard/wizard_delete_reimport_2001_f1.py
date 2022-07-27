# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

class WizardDeleteReimport2001F1(osv.osv_memory):

    _name = 'wizard.delete.reimport.2001.f1'

    def write_info_to_f1(self, cursor, uid, ids, f1_ids, context=None):
        f1_obj = self.pool.get('giscedata.facturacio.importacio.linia')

        for f1_info in f1_obj.read(cursor, uid, f1_ids, ['user_observations']):
            f1_obj.write(cursor, uid, f1_info['id'], {
                'user_observations': "Reimportat mitjançant l'acció de \"(2001) Eliminar "
                "F1 mateix origen i reimportar\"\n{}".format(f1_info['user_observations'] or '')
            })

    def get_duplicated_f1(self, cursor, uid, ids, f1_id, origin, distribuidora_id, context=None):
        f1_obj = self.pool.get('giscedata.facturacio.importacio.linia')
        duplicated_f1_ids = f1_obj.search(cursor, uid,
            [('invoice_number_text','=', origin),('distribuidora_id','=', distribuidora_id),('id','!=', f1_id)]
        )

        delete_ids = []
        error_list = []
        for f1 in f1_obj.browse(cursor, uid, duplicated_f1_ids):
            if f1.state == 'valid' and (not f1.error_ids or '2002' not in [x.name for x in f1.error_ids]):
                error_list.append("Per l'origen {} hi ha un F1 correcte sense warning 2002, ID: {}".format(origin, f1.id))
            else:
                delete_ids.append(f1.id)
        if error_list:
            error_list.append("Per l'origen {} es podrien esborrar els F1 ns {}".format(origin, str(delete_ids)))
            return False, error_list
        return True, delete_ids

    def delete_reimport(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        f1_obj = self.pool.get('giscedata.facturacio.importacio.linia')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_reimport_f1_obj = self.pool.get('giscedata.facturacio.switching.wizard')
        wiz = self.browse(cursor, uid, ids[0])

        selected_ids = context.get('active_ids', [])
        error_msg = []
        f1_to_reimport = []

        for f1 in f1_obj.browse(cursor, uid, selected_ids):

            if f1.state != 'erroni':
                error_msg.append(u"F1 amb origen {} no és erroni".format(f1.invoice_number_text))
                continue

            if not f1.error_ids or '2001' not in [x.name for x in f1.error_ids]:
                error_msg.append(u"F1 amb origen {} no té error 2001".format(f1.invoice_number_text))
                continue

            no_draft_fact = fact_obj.search(cursor, uid, [
                ('origin', '=', f1.invoice_number_text), ('partner_id', '=', f1.distribuidora_id.id),
                ('type', 'in', ['in_invoice','in_refund']), ('state', '!=', 'draft')
            ])

            if no_draft_fact:
                error_msg.append(u"F1 amb origen {} té una factura de proveïdor no en esborrany".format(f1.invoice_number_text))
                continue

            can_continue, result = self.get_duplicated_f1(cursor, uid, ids, f1.id, f1.invoice_number_text, f1.distribuidora_id.id)

            if not can_continue:
                error_msg += result
            else:
                duplicated_f1_ids = result

                if duplicated_f1_ids:
                    f1_obj.unlink(cursor, uid, duplicated_f1_ids)

                draft_fact_ids = fact_obj.search(cursor, uid, [
                    ('origin', '=', f1.invoice_number_text), ('partner_id', '=', f1.distribuidora_id.id),
                    ('type','in', ['in_invoice', 'in_refund']), ('state', '=', 'draft')
                ])

                if draft_fact_ids:
                    fact_obj.unlink(cursor, uid, draft_fact_ids)

                f1_to_reimport.append(f1.id)


        info_msg = u"Errors:\n{}\n\n".format('\n'.join(error_msg))

        if f1_to_reimport:
            self.write_info_to_f1(cursor, uid, ids, f1_to_reimport)
            info_msg += "S'estan reimportant en segon pla els següents F1:\n{}\n\n".format(f1_to_reimport)
            ctx = {'active_ids': f1_to_reimport, 'active_id': f1_to_reimport[0]}
            wiz_reimport_id = wiz_reimport_f1_obj.create(cursor, uid, {}, context=ctx)
            wiz_reimport_f1_obj.sub_action_importar_f1(cursor, uid, [wiz_reimport_id], context=ctx)

        wiz.write({'state':'end','info':info_msg})

    _columns = {
        'state': fields.selection(
            [('init', 'Initial'), ('end', 'End')], 'State'
        ),
        'info': fields.text(_('Informació'))
    }

    _defaults = {
        'state': lambda *a: 'init',
    }

WizardDeleteReimport2001F1()