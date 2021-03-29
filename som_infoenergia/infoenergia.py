# -*- coding: utf-8 -*-
import os, datetime, csv
from dateutil.relativedelta import relativedelta
from paramiko import SSHClient, AutoAddPolicy
import tempfile, shutil
import base64
from scp import SCPClient
import shutil
from StringIO import StringIO

from autoworker import AutoWorker
from oorq.decorators import job, create_jobs_group
from osv import fields, osv
from tools.translate import _
from tools import config
from som_infoenergia.pdf_tools import topdf


ESTAT_LOT = [
    ('esborrany','Esborrany'),
    ('obert', 'Obert'),
    ('realitzat', 'Realitzat'),
]

TIPUS_INFORME = [
    ('m1', 'M1 terciari'),
    ('m2', 'M2 domèstic'),
    ('m5', 'M5 domèstic'),
    ('m6_domestic', 'M6 domèstic'),
    ('m6_terciari', 'M6 terciari'),
    ('m10', 'M10 terciari'),
    ('m11', 'M11 domèstic'),
    ('fv', 'FV (fotovoltaic)'),
    ('altres', 'Altres'),
]


def get_ssh_connection():
    beedata_user = config.get(
        "beedata_ssh_user", "")
    beedata_password = config.get(
        "beedata_ssh_password", "")
    beedata_host = config.get(
        "beedata_ssh_host", "")
    beedata_port = config.get(
        "beedata_ssh_port", "22")

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy)

    ssh.connect(hostname=beedata_host,
                port=beedata_port,
                username=beedata_user,
                password=beedata_password)
    return ssh

class SomInfoenergiaLotEnviament(osv.osv):
    _name = 'som.infoenergia.lot.enviament'

    def _attach_csv(self, cursor, uid, ids, filepath):
        if isinstance(ids, (tuple, list)):
                ids = ids[0]
        attachment_obj = self.pool.get('ir.attachment')
        attachment_to_delete = attachment_obj.search(cursor, uid,
            [('res_id', '=', ids), ('res_model', '=', 'som.infoenergia.lot.enviament')])

        with open(filepath, 'r') as pdf_file:
            data = pdf_file.read()
            values = {
                'name': 'Enviaments.csv',
                'datas': base64.b64encode(data),
                'res_model': 'som.infoenergia.lot.enviament',
                'res_id': ids
            }
            attachment_id = attachment_obj.create(cursor, uid, values)

        attachment_obj.unlink(cursor, uid, attachment_to_delete)

        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.unlink(filepath)
        return attachment_id

    def create_enviaments_from_attached_csv(self, cursor, uid, ids, attach_id, context=None):

            attachment_obj = self.pool.get('ir.attachment')
            attach_data = attachment_obj.read(cursor,uid, attach_id, ['datas'])['datas']
            csv_file = StringIO(base64.b64decode(attach_data))
            headers = [
                h.lower()
                for h in csv.reader(csv_file, delimiter=';', quotechar='"').next()
            ]

            csv_dictReader = csv.DictReader(csv_file, delimiter=';', quotechar='"', fieldnames=headers, restkey="wrong_row")
            csv_data = list(csv_dictReader)
            self.write(cursor, uid, ids, {'number_csv_rows': len(csv_data)})

            self.create_enviaments_from_csv(cursor, uid, ids, csv_data)

    def create_enviaments_from_csv(self, cursor, uid, ids, csv_data, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        for idx, env in enumerate(csv_data):
            self.create_single_enviament_async(cursor, uid, ids, env)

        return idx

    @job(queue="infoenergia_download")
    def create_single_enviament_async(self, cursor, uid, ids, env_data, context=None):
        self.create_single_enviament(cursor, uid, ids, env_data, context)

    def create_single_enviament(self, cursor, uid, ids, env_data, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        pol_obj = self.pool.get('giscedata.polissa')
        env_obj = self.pool.get('som.infoenergia.enviament')

        pol_ids = pol_obj.search(cursor, uid, [('name','=',env_data['contractid'])]) if env_data['contractid'] != "True" else None
        msg = ""
        env_values = {
            'polissa_id': pol_ids[0] if pol_ids else None,
            'pdf_filename': env_data['report'],
            'num_polissa_csv': env_data['contractid'],
            'body_text': env_data['text'],
            'lot_enviament': ids,
            'estat': 'esborrany'
        }
        if not pol_ids:
            pol_inactive_ids = pol_obj.search(cursor, uid, [('name','=',env_data['contractid']), ('active','=',False)]) if env_data['contractid'] != "True" else None
            if pol_inactive_ids:
                env_values['polissa_id'] = pol_inactive_ids[0]
                env_values['estat'] = 'cancellat'
                msg += 'La pòlissa {} està donada de baixa. '.format(env_values['num_polissa_csv'])
            else:
                env_values['estat'] = 'error'
                msg += 'No s\'ha trobat la pòlissa {}. '.format(env_values['num_polissa_csv'])

        env_id = env_obj.search(cursor, uid, [('lot_enviament','=',ids), ('pdf_filename', '=', env_data['report'])])
        if "wrong_row" in env_data:
            env_values['estat'] = 'error'
            msg += 'La línia del csv té un format incorrecte: {}. '.format(env_data)
        if not env_data['valid']:
            env_values['estat'] = 'error'
            msg += 'Informe marcat "no vàlid" al csv. '

        if env_id:
            msg += "Dades actualitzades. "
            env_obj.write(cursor, uid,env_id[0], env_values, context)
        else:
            env_id = env_obj.create(cursor, uid, env_values, context)

        if msg:
            env_obj.add_info_line(cursor, uid, env_id, msg)

        return True

    def add_info_line(self, cursor, uid, ids, new_info, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        lot = self.browse(cursor, uid, ids)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        info = lot.info if lot.info else ''
        lot.write({'info': str(now) + ': ' + new_info + '\n' + info})

    def get_csv(self, cursor, uid, ids, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        lot_obj = self.pool.get('som.infoenergia.lot.enviament')
        lot = lot_obj.browse(cursor, uid, ids)

        try:
            ssh = get_ssh_connection()
            output_dir = config.get(
                "infoenergia_report_download_dir", "/tmp/test_shera/reports")

            csv_path_file = lot.csv_path_file
            output_filepath = os.path.join(output_dir, 'Enviaments.csv')

            scp = SCPClient(ssh.get_transport())
            scp.get(csv_path_file, output_filepath)

            attachment_id = self._attach_csv(cursor, uid, ids, output_filepath)
            lot.create_enviaments_from_attached_csv(attachment_id)

            self.add_info_line(cursor, uid, ids, 'CSV descarregat correctament')
        except Exception as e:
            message = 'ERROR ' + str(e)
            self.add_info_line(cursor, uid, ids, message)

    def _ff_totals(self, cursor, uid, ids, field_name, arg,
                             context=None):
        res = {}
        env_obj = self.pool.get('som.infoenergia.enviament')
        if field_name == 'total_enviaments':
            for _id in ids:
                res[_id] = env_obj.search_count(cursor, uid,
                                        [('lot_enviament.id', '=', _id)])
        else:
            estats = {
                'total_enviats': 'enviat',
                'total_oberts': 'obert',
                'total_esborrany': 'esborrany',
                'total_cancelats': 'cancellat',
                'total_errors': 'error',
                'total_encuats': 'encuat',

            }
            for _id in ids:
                res[_id] = env_obj.search_count(cursor, uid,
                                        [('lot_enviament.id', '=', _id),('estat','=',estats[field_name])])
        return res

    def _ff_progress(self, cursor, uid, ids, field_name, arg,
                             context=None):
        res = {}
        for _id in ids:
            number_csv_rows = float(self.read(cursor, uid, _id, ['number_csv_rows'])['number_csv_rows'])
            if not number_csv_rows:
                res[_id] = 0
            elif field_name == 'env_creation_progress':
                total_enviaments = self.read(cursor, uid, _id, ['total_enviaments'])['total_enviaments']
                res[_id] = (total_enviaments / number_csv_rows) * 100
            elif field_name == 'pdf_download_progress':
                # TODO: comprovar si el progrés dels PDF es pot fer millor
                lot_values = self.read(cursor, uid, _id,
                    ['total_enviats', 'total_oberts', 'total_cancelats', 'total_errors','total_encuats']
                )
                denominador = float(number_csv_rows - lot_values['total_cancelats'] - lot_values['total_errors'])
                if denominador == 0:
                    res[_id] = 0
                else:
                    res[_id] = 100 * (lot_values['total_oberts'] + lot_values['total_enviats'] + lot_values['total_encuats']) / denominador
            elif field_name == 'env_sending_progress':
                lot_values = self.read(cursor, uid, _id,
                    ['total_enviats', 'total_cancelats', 'total_errors', 'number_csv_rows']
                )
                denominador = float(number_csv_rows - lot_values['total_cancelats'] - lot_values['total_errors'])
                if denominador == 0:
                    res[_id] = 0
                else:
                    res[_id] = (lot_values['total_enviats'] / denominador) * 100
        return res

    _columns = {
        'name': fields.char(_('Nom del lot'), size=256, required=True),
        'estat': fields.selection(ESTAT_LOT, _('Estat'),
            required=True),
        'is_test': fields.boolean('Test',
            help=_(u"És un enviament de prova?")),
        'tipus_informe': fields.selection(TIPUS_INFORME, _('Tipus d\'informe'),
            required=True),
        'info': fields.text(_(u'Informació Adicional'),
            help=_(u"Inclou qualsevol informació adicional, com els errors del Shera")),
        'email_template': fields.many2one(
            'poweremail.templates', 'Plantilla del correu del lot', required=True,
            domain="[('object_name.model', '=', 'som.infoenergia.enviament')]"
        ),
        'pdf_path_folder': fields.char(_('Ruta carpeta dels PDFs'), size=256),
        'csv_path_file': fields.char(_('Ruta fitxer CSV'), size=256),
        'total_enviaments': fields.function(
            _ff_totals, string='Enviaments totals', readonly=True,
            type='integer', method=True),
        'total_enviats': fields.function(
            _ff_totals, string='Enviaments enviats', readonly=True,
            type='integer', method=True
        ),
        'total_encuats': fields.function(
            _ff_totals, string='Enviaments encuats per enviar', readonly=True,
            type='integer', method=True, help="S'ha realitzat l'acció d'enviar i el procés en segon pla té la tasca pendent"
        ),
        'total_oberts': fields.function(
            _ff_totals, string='Enviaments oberts', readonly=True,
            type='integer', method=True, help="Enviaments que tenen el PDF adjunt i encara no s'han enviat"
        ),
        'total_esborrany': fields.function(
            _ff_totals, string='Enviaments en esborrany (sense PDF)', readonly=True,
            type='integer', method=True
        ),
        'total_cancelats': fields.function(
            _ff_totals, string='Enviaments cancel·lats', readonly=True,
            type='integer', method=True,
            help="Ja sigui perquè la pòlissa està de baixa, té l'enviament deshabilitat..."
        ),
        'total_errors': fields.function(
            _ff_totals, string='Enviaments amb error', readonly=True,
            type='integer', method=True
        ),
        'env_creation_progress': fields.function(
            _ff_progress, string='Progrés de la creació dels enviaments del lot', readonly=True,
            type='float', method=True
        ),
        'pdf_download_progress': fields.function(
            _ff_progress, string='Progrés de la descàrrega de PDFs', readonly=True,
            type='float', method=True
        ),
        'env_sending_progress': fields.function(
            _ff_progress, string='Progrés de l\'enviament de les línies d\'enviament', readonly=True,
            type='float', method=True
        ),
        'number_csv_rows': fields.integer(
            'Número total de files del CSV', readonly=True
        ),
    }

    _defaults = {
        'estat': lambda *a: 'obert',
        'is_test': lambda *a: False,
        'number_csv_rows': lambda *a: 0,
        'env_sending_progress': lambda *a: 0,
        'pdf_download_progress': lambda *a: 0,
        'env_sending_progress': lambda *a: 0,
    }

SomInfoenergiaLotEnviament()


ESTAT_ENVIAT = [
    ('esborrany','Esborrany'),
    ('obert', 'Obert'),
    ('error', 'Error'),
    ('encuat', 'Encuat per enviar'),
    ('enviat', 'Enviat'),
    ('cancellat', 'Cancel·lat')
]

QUALITAT = [
    ('tou', 'TOU'),
    ('cch', 'CCH')
]

ANTIGUITAT = [
    ('1r', 'Primer any'),
    ('2n', 'Segon any'),
    ('3r', 'Tercer any'),
]


class SomInfoenergiaEnviament(osv.osv):
    _name = 'som.infoenergia.enviament'

    def _attach_pdf(self, cursor, uid, ids, filepath):
        if isinstance(ids, (tuple, list)):
                ids = ids[0]
        enviament = self.browse(cursor, uid, ids)
        attachment_obj = self.pool.get('ir.attachment')
        attachment_to_delete = attachment_obj.search(cursor, uid,
            [('res_id', '=', ids), ('res_model', '=', 'som.infoenergia.enviament')])

        with open(filepath, 'r') as pdf_file:
            data = pdf_file.read()
            values = {
                'name':'Lot {}, informe {}, contracte {}'.format(
                        enviament.lot_enviament.name, enviament.lot_enviament.tipus_informe.upper(), enviament.polissa_id.name
                    ),
                'datas_fname': '{}_{}.pdf'.format(enviament.polissa_id.name, enviament.lot_enviament.tipus_informe.upper()),
                'datas': base64.b64encode(data),
                'res_model': 'som.infoenergia.enviament',
                'res_id': ids
            }
            attachment_obj.create(cursor, uid, values)

        attachment_obj.unlink(cursor, uid, attachment_to_delete)

        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.unlink(filepath)

    def add_info_line(self, cursor, uid, ids, new_info, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        env = self.browse(cursor, uid, ids)

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        info = env.info if env.info else ''
        env.write({'info': str(now) + ': ' + new_info + '\n' + info})

    @job(queue="infoenergia_download")
    def download_pdf(self, cursor, uid, ids, context):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        env_obj = self.pool.get('som.infoenergia.enviament')

        env = env_obj.browse(cursor, uid, ids)

        if not env.polissa_id:
            env.write({'estat': 'error'})
            message = u'ERROR: No es pot descarregar el PDF perque l\'enviament no té cap pòlissa associada'
            self.add_info_line(cursor, uid, ids, message, context)
            return

        try:
            ssh = get_ssh_connection()
            output_dir = config.get(
                "infoenergia_report_download_dir", "/tmp/test_shera/reports")
            pdf_path_folder = env.lot_enviament.pdf_path_folder

            download_filepath = os.path.join(pdf_path_folder, env.pdf_filename)
            output_filepath = os.path.join(output_dir, env.pdf_filename)

            scp = SCPClient(ssh.get_transport())
            scp.get(download_filepath, output_filepath)

            self.render_header_data(cursor, uid, ids, output_filepath, output_dir)

            self._attach_pdf(cursor, uid, ids, output_filepath)
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            env.write({'estat': 'obert','data_informe':now})
            self.add_info_line(cursor, uid, ids, 'PDF descarregat correctament', context)
        except Exception as e:
            env.write({'estat': 'error'})
            message = 'ERROR ' + str(e)
            self.add_info_line(cursor, uid, ids, message, context)

    def render_header_data(self, cursor, uid, env_id, pdf_filepath, output_dir, context=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_name = os.path.join(base_dir, os.path.join('report', 'infoenergia_header.mako'))
        enviament = self.browse(cursor, uid, env_id)
        pol_obj = self.pool.get('giscedata.polissa')
        partner_obj = self.pool.get('res.partner')

        dades_linia_enviament = {
                    'contract_name': enviament.polissa_id.name,
                    'report': pdf_filepath,
                    }
        pol_data = pol_obj.read(cursor, uid, enviament.polissa_id.id, ['cups', 'titular', 'cups_direccio', 'persona_fisica'])
        name_surnames = pol_data['titular'][1]
        if pol_data['persona_fisica'] == 'NI':
            name_surnames = partner_obj.separa_cognoms(cursor, uid, name_surnames)
            dades_linia_enviament.update({
                'name': name_surnames['nom'],
                'surname': ' '.join(name_surnames['cognoms'])
            })
        else:
            dades_linia_enviament.update({'name': name_surnames, 'surname':''})

        dades_linia_enviament.update({
            'cups': pol_data['cups'][1],
            'address': pol_data['cups_direccio'],
            'lang': partner_obj.read(cursor, uid, pol_data['titular'][0], ['lang'])['lang']
        })

        path_aux = tempfile.mkdtemp()
        try:
            new_report = topdf.customize(
                report = dades_linia_enviament,
                template_name = template_name,
                path_aux = path_aux,
                path_output = output_dir
            )
            with open(new_report, 'rb') as report_file:
                pdf_data = base64.b64encode(report_file.read())

            if not pdf_data:
                raise Exception('Null report pdf content')
        except Exception as e:
            raise Exception("Render Header Failed: " + str(e))
        shutil.rmtree(path_aux)


    def send_reports(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if not ids:
            return
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        lot_name = self.read(cursor, uid, ids[0],['lot_enviament'])['lot_enviament'][1]
        job_ids = []
        for _id in ids:
            j = self.send_single_report_async(
                cursor, uid, _id, context
            )
            job_ids.append(j.id)
        create_jobs_group(
            cursor.dbname, uid, _('Enviament Infoenergia Lot {} - {} enviaments').format(
                lot_name, len(ids)
            ), 'infoenergia.infoenergia_send', job_ids
        )
        amax_proc = int(self.pool.get("res.config").get(cursor, uid, "infoenergia_send_tasks_max_procs", "0"))
        if not amax_proc:
            amax_proc = None
        aw = AutoWorker(queue='infoenergia_send', default_result_ttl=24 * 3600, max_procs=amax_proc)
        aw.work()

    def send_single_report(self, cursor, uid, _id, context=None):
        if context is None:
            context = {}

        if isinstance(_id, (tuple, list)):
            _id = _id[0]

        pe_send_obj = self.pool.get('poweremail.send.wizard')
        attach_obj = self.pool.get('ir.attachment')
        enviament = self.browse(cursor, uid, _id, context=context)
        allowed_states = ['obert']
        if context.get('allow_reenviar', False):
            allowed_states.append('enviat')
        if enviament.estat not in allowed_states:
            return

        polissa = enviament.polissa_id

        if not polissa.emp_allow_recieve_mail_infoenergia:
            message = u"INFO: La pòlissa no té habilitada la opció de rebre correus d'Infoenergia"
            enviament.write({'estat': 'cancellat'})
            self.add_info_line(cursor, uid, _id, message, context)
            return

        attachment_id = attach_obj.search(cursor, uid,
        [('res_id', '=', _id), ('res_model', '=', 'som.infoenergia.enviament')])
        if attachment_id:
            attachment_id = attachment_id[0]
        else:
            message = u"ERROR: No es pot enviar el report perquè no s'ha trobat l'adjunt"
            enviament.write({'estat': 'error'})
            self.add_info_line(cursor, uid, _id, message, context)
            return
        if not polissa.active or polissa.data_baixa:
            message = u"INFO: La pòlissa està inactiva o té data de baixa"
            enviament.write({'estat': 'cancellat'})
            self.add_info_line(cursor, uid, _id, message, context)
            return

        template_id = enviament.lot_enviament.email_template.id

        tmpl = enviament.lot_enviament.email_template

        ctx = context.copy()
        ctx.update({
            'src_rec_ids': [_id],
            'src_model': 'som.infoenergia.enviament',
            'template_id': template_id,
            'active_id': _id,
        })
        send_id = pe_send_obj.create(cursor, uid, {}, context=ctx)
        vals = {'from': tmpl.enforce_from_account.id,
                'attachment_ids': [(6, 0, [attachment_id])]}
        if context.get('email_to', False):
            vals.update({'to':context.get('email_to')})
            vals.update({'bcc':''})
        if context.get('email_subject', False):
            vals.update({'subject': context.get('email_subject')})
        pe_send_obj.write(cursor, uid, [send_id], vals, context=ctx)
        sender = pe_send_obj.browse(cursor, uid, send_id, context=ctx)
        sender.send_mail(context=ctx)

    @job(queue="infoenergia_send")
    def send_single_report_async(self, cursor, uid, id, context=None):
        self.send_single_report(cursor, uid, id, context)

    def poweremail_create_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan es creei un email
        a partir d'un enviament.
        """
        for _id in ids:
            self.write(cursor, uid, _id, {'estat':'encuat'})
            self.add_info_line(cursor, uid, _id, "INFO: Correu encuat per enviar", context)
        return True

    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan es modifiqui un email.
        """
        if context is None:
            context = {}
        if 'date_mail' in vals and 'folder' in vals:
            vals_w = {
                    'date_sent': vals['date_mail'],
                    'folder': vals['folder']
                }
            if vals_w['folder'] == 'sent':
                for _id in ids:
                    self.write(cursor, uid, _id, {'estat':'enviat', 'data_enviament': vals_w['date_sent']})
                    self.add_info_line(cursor, uid, _id, "INFO: Correu enviat", context)
        return True


    _columns = {
        'polissa_id': fields.many2one('giscedata.polissa', _('Contracte'),
            translate=True,
            ondelete='restrict',
            select=True, pol_rel='no'),
        'lang': fields.related('polissa_id', 'titular', 'lang',
            type='char',
            help=_("Idioma del partner titular de la pòlissa"),
            string=_('Idioma'),
            readonly=True),
        'name': fields.related('polissa_id', 'name',
            type='char',
            string=_('Num Polissa'),
            readonly=True),
        'estat': fields.selection(ESTAT_ENVIAT, _('Estat'),
            required=True),
        'lot_enviament': fields.many2one('som.infoenergia.lot.enviament', _('Lot Enviament'),
            required=True,
            ondelete='restrict',
            select=True),
        'tipus_informe_lot': fields.related('lot_enviament', 'tipus_informe',
            type='char',
            string=_('Tipus d\'informe lot'),
            readonly=True),
        'antiguitat': fields.selection(ANTIGUITAT, _('Any de l\'informe'), size=256, allow_none=True),
        'qualitat': fields.selection(QUALITAT, _('Qualitat de les dades'), size=256, allow_none=True),
        'data_enviament':  fields.date(_("Data enviament"), allow_none=True),
        'data_informe':  fields.date(_("Data de l'informe"), allow_none=True),
        'pdf_filename': fields.char(_('Nom fitxer PDF'), size=256),
        'info': fields.text(_(u'Informació Adicional'),
            help=_(u"Inclou qualsevol informació adicional, com els errors del Shera")),
        'num_polissa_csv': fields.char(_('Número contracte CSV Beedata'), size=10),
        'body_text': fields.text(_(u"Cos de l'e-mail enviat per Beedata"))
    }

    _defaults = {
        'estat': lambda *a: 'esborrany',
    }

SomInfoenergiaEnviament()
