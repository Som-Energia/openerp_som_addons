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
                port=int(beedata_port),
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

            self.create_enviaments_from_csv(cursor, uid, ids, csv_data, context)

    def create_enviaments_from_polissa_list(self, cursor, uid, ids, polissa_ids, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        job_ids = []
        for pol_id in polissa_ids:
            job = self.create_single_enviament_from_polissa_async(cursor, uid, ids, pol_id, context=context)
            job_ids.append(job.id)
            # Create a jobs_group to see the status of the operation
        create_jobs_group(
            cursor.dbname, uid,
            _('Crear Enviaments al lot amb ID {0} a partir de {1} polisses.').format(ids, len(job_ids)),
            'infoenergia.create_enviaments', job_ids
        )
        amax_proc = int(self.pool.get("res.config").get(cursor, uid, "infoenergia_create_enviaments_tasks_max_procs", "0"))
        if not amax_proc:
            amax_proc = None
        aw = AutoWorker(queue="infoenergia_create_enviament", default_result_ttl=24 * 3600, max_procs=amax_proc)
        aw.work()

        return True

    @job(queue="infoenergia_create_enviament")
    def create_single_enviament_from_polissa_async(self, cursor, uid, ids, polissa_id, context=None):
        self.create_single_enviament_from_polissa(cursor, uid, ids, polissa_id, context)

    def create_single_enviament_from_polissa(self, cursor, uid, ids, polissa_id, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        env_obj = self.pool.get('som.infoenergia.enviament')
        env_values = {
            'polissa_id': polissa_id,
            'lot_enviament': ids,
            'estat': 'preesborrany',
        }
        env_id = env_obj.search(cursor, uid, [('lot_enviament','=',ids), ('polissa_id', '=', polissa_id)])
        if not env_id:
            env_id = env_obj.create(cursor, uid, env_values, context)
            env_obj.add_info_line(cursor, uid, env_id, u'Enviament creat des de pòlissa')

    def create_enviaments_from_csv(self, cursor, uid, ids, csv_data, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        for idx, env in enumerate(csv_data):
            self.create_single_enviament_async(cursor, uid, ids, env, context)

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
            'pdf_filename': context.get('path_pdf', '') + "/" + env_data['report'],
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

        env_id = env_obj.search(cursor, uid, [('lot_enviament','=',ids), ('polissa_id', '=', env_values['polissa_id'])])
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

            csv_path_file = context.get('path_csv','')
            output_filepath = os.path.join(output_dir, 'Enviaments.csv')

            scp = SCPClient(ssh.get_transport())
            scp.get(csv_path_file, output_filepath)

            attachment_id = self._attach_csv(cursor, uid, ids, output_filepath)
            lot.create_enviaments_from_attached_csv(attachment_id, context)

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
        elif field_name == 'total_env_csv':
            for _id in ids:
                res[_id] = env_obj.search_count(cursor, uid,
                                        [('lot_enviament.id', '=', _id), ('pdf_filename','!=','')])
        else:
            estats = {
                'total_preesborrany': 'preesborrany',
                'total_esborrany': 'esborrany',
                'total_oberts': 'obert',
                'total_enviats': 'enviat',
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
        env_obj = self.pool.get('som.infoenergia.enviament')
        for _id in ids:
            total_enviaments = float(self.read(cursor, uid, _id, ['total_enviaments'])['total_enviaments'])
            if not total_enviaments:
                res[_id] = 0
            elif field_name == 'env_csv_progress':
                total_env_csv = self.read(cursor, uid, _id, ['total_env_csv'])['total_env_csv']
                res[_id] = (total_env_csv / total_enviaments) * 100
            elif field_name == 'pdf_download_progress':
                # TODO: comprovar si el progrés dels PDF es pot fer millor
                total_env_amb_pdf = env_obj.search_count(cursor, uid,
                                        [('lot_enviament.id', '=', _id), ('data_informe', '!=', False)])
                res[_id] = (total_env_amb_pdf / total_enviaments) * 100
            elif field_name == 'env_sending_progress':
                total_env_enviats = env_obj.search_count(cursor, uid,
                                        [('lot_enviament.id', '=', _id), ('data_enviament', '!=', False)])
                res[_id] = (total_env_enviats / total_enviaments) * 100
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
        'total_env_csv': fields.function(_ff_totals,
            string='Enviaments presents en CSVs',
            help="Enviaments que han estat informats en algun CSV descarregat de Beedata", readonly=True,
            type='integer', method=True
        ),
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
        'total_preesborrany': fields.function(
            _ff_totals, string='Enviaments en pre-esborrany (creats des de pòlissa)',
            help="Enviaments que s'han creat des d'una pòlissa i no s'han descarregat en cap CSV", readonly=True,
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
        'env_csv_progress': fields.function(
            _ff_progress, string='Enviaments informats en algun CSV descarregat', readonly=True,
            type='float', method=True, help="Indica quants enviaments s'han trobat en algun CSV descarregat de Beedata"
        ),
        'pdf_download_progress': fields.function(
            _ff_progress, string='Enviaments amb PDF descarregat', readonly=True,
            type='float', method=True, help="Indica quants PDFs s'han descarregat del total d'enviaments del Lot"
        ),
        'env_sending_progress': fields.function(
            _ff_progress, string='Enviaments enviats', readonly=True,
            type='float', method=True, help="Indica quants enviaments s'han enviat del total d'enviaments del Lot"
        ),
    }

    _defaults = {
        'estat': lambda *a: 'obert',
        'is_test': lambda *a: False,
        'env_csv_progress': lambda *a: 0,
        'pdf_download_progress': lambda *a: 0,
        'env_sending_progress': lambda *a: 0,
    }

SomInfoenergiaLotEnviament()

