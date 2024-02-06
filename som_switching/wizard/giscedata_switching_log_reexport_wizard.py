# -*- encoding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import os
from datetime import datetime
import zipfile
import base64


class WizardReexportLogAttachment(osv.osv_memory):
    _name = 'wizard.giscedata.switching.log.reexport'

    def _get_default_msg(self, cursor, uid, context=None):
        if context is None:
            context = {}
        log_ids = context.get('active_ids', [])
        return _(u"Es reexportaràn {} arxius".format(len(log_ids)))

    def _create_working_directory(self, cursor, uid, ids, context=None):
        """
        Creates the working directory and returns it's name
        """
        temporal_folder_name = '/tmp/wizard_reexportar_log_{}'.format(
            datetime.strftime(datetime.today(), '%Y%m%d%H%M%S.%f'))
        os.makedirs(temporal_folder_name)
        return temporal_folder_name

    def _zip_xml_files(self, cursor, uid, ids, folder, generated_files):
        zip_path = "{}/{}".format(folder, 'casos_exportats.zip')
        with zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for file in generated_files:
                zf.writestr(file[0], file[1])

        return zip_path

    def reexport_files(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        wizard = self.browse(cursor, uid, ids[0], context=context)
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
        log_vals = log_obj.read(cursor, uid, log_ids, [
                                'pas', 'proces', 'request_code', 'cups_text'])
        generated_files = []
        for log in log_vals:
            sw_id = sw_obj.search(cursor, uid, [('codi_sollicitud', '=', log['request_code'])])
            if not sw_id:
                failed_files.append(
                    (log['cups_text'], ("No s'ha trobat un cas amb aquest codi de ",
                                        "solicitud {}".format(log['request_code']))))
                continue
            proces_id = proces_obj.search(cursor, uid, [('name', '=', log['proces'])])
            pas_obj = self.pool.get('giscedata.switching.{}.{}'.format(
                log['proces'].lower(), log['pas']))
            pas_id = pas_obj.search(cursor, uid, [('sw_id', '=', sw_id)])
            try:
                step_id = step_obj.search(cursor, uid,
                                          [('name', '=', log['pas']),
                                           ('proces_id', '=', proces_id[0])])
                xml = sw_obj.exportar_xml(
                    cursor, uid, sw_id[0], step_id[0], pas_id[0], context=context)
                generated_files.append(xml)
            except Exception as e:
                e_string = str(e)
                if not e_string:
                    e_string = e.value
                failed_files.append((log['cups_text'], e_string))
        info = _(u"S'han processat {} fitxers.\n".format(len(log_vals)))
        if failed_files:
            info += _(u"S'han produït els següents errors en els arxius exportats:\n")
            for failed_f in failed_files:
                info += _(u"\t- CUPS {} -> Error: {}\n".format(failed_f[0], failed_f[1]))

        folder = self._create_working_directory(cursor, uid, ids)
        zip_file = self._zip_xml_files(cursor, uid, ids, folder, generated_files)
        f = open(zip_file, 'rb')
        out = f.read()
        f.close()

        wizard.write({
            'report': base64.encodestring(out),
            'filename': zip_file.split('/')[-1],
        })
        wizard.write({'state': 'end', 'msg': info}, context=context)

    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'msg': fields.text('Missatge'),
        'report': fields.binary('Fichero a descargar'),
        'filename': fields.char('Nombre fichero exportado', size=256),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'msg': _get_default_msg,
    }


WizardReexportLogAttachment()
