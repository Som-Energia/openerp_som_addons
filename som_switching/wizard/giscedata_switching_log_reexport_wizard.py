# -*- encoding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardReexportLogAttachment(osv.osv_memory):
    _name = 'wizard.giscedata.switching.log.reexport'

    def _get_default_msg(self, cursor, uid, context=None):
        if context is None:
            context = {}
        log_ids = context.get('active_ids', [])
        return _(u"Es reexportaràn {} arxius".format(len(log_ids)))

    def reexport_files(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        log_ids = context.get('active_ids', False)

        if not log_ids:
            raise osv.except_osv('Error', _('No s\'han seleccionat ids'))
        log_obj = self.pool.get('giscedata.switching.log')
        sw_obj = self.pool.get('giscedata.switching')
        step_obj = self.pool.get('giscedata.switching.step')
        proces_obj = self.pool.get('giscedata.switching.proces')

        context.update({
            'update_logs': True
        })
        failed_files = []
        log_vals = log_obj.read(cursor, uid, log_ids, ['status', 'pas', 'proces', 'request_code'])
        for log in log_vals:
            if log['status'] == 'correcte':
                continue
            sw_id = sw_obj.search(cursor, uid, [('codi_sollicitud', '=', log['request_code'])])
            proces_id = proces_obj.search(cursor, uid, [('name', '=', log['proces'])])
            pas_obj = self.pool.get('giscedata.switching.{}.{}'.format(
                log['proces'].lower(), log['pas']))
            pas_id = pas_obj.search(cursor, uid, [('sw_id', '=', sw_id)])
            try:
                step_id = step_obj.search(cursor, uid,
                                          [('name', '=', log['pas']), ('proces_id', '=', proces_id[0])])
                sw_obj.exportar_xml(cursor, uid, sw_id[0], step_id[0], pas_id[0], context=context)
            except Exception, e:
                e_string = str(e)
                if not e_string:
                    e_string = e.value
                failed_files.append((fname, e_string))
        info = _(u"S'han processat {} fitxers.\n".format(len(log_vals)))
        if failed_files:
            info += _(u"S'han produït els següents errors en els arxius exportats:\n")
            for failed_f in failed_files:
                info += _(u"\t- Fitxer {} -> Error: {}\n".format(failed_f[0], failed_f[1]))

        self.write(cursor, uid, ids, {'state': 'end', 'msg': info}, context=context)

    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'msg': fields.text('Missatge')
    }

    _defaults = {
        'state': lambda *a: 'init',
        'msg': _get_default_msg,
    }


WizardReexportLogAttachment()
