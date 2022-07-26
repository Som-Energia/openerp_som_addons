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



ESTAT_ENVIAT = [
    ('preesborrany', "Pre Esborrany"),
    ('esborrany','Esborrany'),
    ('obert', 'Obert'),
    ('error', 'Error'),
    ('encuat', 'Encuat per enviar'),
    ('enviat', 'Enviat'),
    ('cancellat', 'Cancel·lat'),
    ('baixa', 'Baixa'),
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
                'datas_fname': '{}_{}.pdf'.format(enviament.polissa_id.name, enviament.lot_enviament.name),
                'datas': base64.b64encode(data),
                'res_model': 'som.infoenergia.enviament',
                'res_id': ids
            }
            attachment_obj.create(cursor, uid, values)

        attachment_obj.unlink(cursor, uid, attachment_to_delete)

        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.unlink(filepath)

    def add_info_line(self, cursor, uid, ids, new_info, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        for env_id in ids:
            env = self.browse(cursor, uid, env_id)
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            info = env.info if env.info else ''
            env.write({'info': str(now) + ': ' + new_info + '\n' + info})

    @job(queue="infoenergia_download")
    def download_pdf(self, cursor, uid, ids, context):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        env_obj = self.pool.get('som.infoenergia.enviament')

        env = env_obj.browse(cursor, uid, ids)
        to_download = ['esborrany']
        if context.get('force_download_pdf', False):
            to_download.append('obert')

        if not env.polissa_id:
            env.write({'estat': 'error'})
            message = u'ERROR: No es pot descarregar el PDF perque l\'enviament no té cap pòlissa associada'
            self.add_info_line(cursor, uid, ids, message, context)
            return
        if env.estat not in to_download:
            return
        try:
            ssh = get_ssh_connection()
            output_dir = config.get(
                "infoenergia_report_download_dir", "/tmp/test_shera/reports")
            pdf_name = env.pdf_filename.split("/")[-1]
            output_filepath = os.path.join(output_dir, pdf_name)

            scp = SCPClient(ssh.get_transport())
            scp.get(env.pdf_filename, output_filepath)

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

        if not job_ids:
            return False

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
            message = u"La pòlissa no té habilitada la opció de rebre correus d'Infoenergia"
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
            message = u"La pòlissa està inactiva o té data de baixa"
            enviament.write({'estat': 'baixa'})
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
        origin_ids = context.get('pe_callback_origin_ids', {})
        for _id in ids:
            self.write(cursor, uid, _id, {'estat':'encuat', 'mail_id': origin_ids.get(_id, False)})
            self.add_info_line(cursor, uid, _id, "Correu encuat per enviar", context)
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
                    self.add_info_line(cursor, uid, _id, "Correu enviat", context)
        return True

    def poweremail_unlink_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan s'esborra un email
        d'un enviament.
        """
        for _id in ids:
            self.write(cursor, uid, _id, {'estat':'obert'})
            self.add_info_line(cursor, uid, _id, "Correu eliminat de la bústia", context)
        return True

    def resend_email(self, cursor, uid, id, context=None):
        md_obj = self.pool.get('ir.model.data')
        view_id = md_obj.get_object_reference(
            cursor, uid, 'poweremail', 'poweremail_mailbox_form')[1]
        mail_id = self.read(cursor, uid, id[0], ['mail_id'])['mail_id'][0]
        return {
            'name': 'Reenviar',
            'view_type':'form',
            'view_mode':'form',
            #'views' : [(view_id,'form')],
            'res_model':'poweremail.mailbox',
            'view_id':False,
            #'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id': mail_id,
            'target': 'new',
            #'context': context,
        }


    def _ff_te_autoconsum(self, cursor, uid, ids, field_name, args, context):
        res = {}
        gp_obj = self.pool.get('giscedata.polissa')
        for item in ids:
            pol = self.read(cursor, uid, item, ['polissa_id'])
            if not 'polissa_id' in pol or not pol['polissa_id']:
                res[item] = False
            else:
                auto_type = gp_obj.read(cursor, uid, pol['polissa_id'][0], ['autoconsumo'])['autoconsumo']
                res[item] = auto_type != '00'

        return res

    _columns = {
        'polissa_id': fields.many2one('giscedata.polissa', _('Contracte'),
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
        'autoconsum': fields.function(
            _ff_te_autoconsum, store=True, type='boolean', string=_("Té Autoproducció"),
            readonly=True, method=True),
        'tarifa': fields.related('polissa_id', 'tarifa', 'name',
            type='char',
            string=_('Tarifa'),
            readonly=True),
        'estat': fields.selection(ESTAT_ENVIAT, _('Estat'),
            required=True),
        'lot_enviament': fields.many2one('som.infoenergia.lot.enviament', _('Lot Enviament'),
            required=True,
            ondelete='restrict',
            select=True),
        'mail_id': fields.many2one(
            'poweremail.mailbox', 'Mail', ondelete='set null'
        ),
        'tipus_informe_lot': fields.related('lot_enviament', 'tipus_informe',
            type='char',
            string=_('Tipus d\'informe lot'),
            readonly=True),
        'found_in_search': fields.boolean(_("La pòlissa relacionada estava present a alguna cerca")),
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
        'found_in_search': lambda *a: False,
    }

SomInfoenergiaEnviament()
