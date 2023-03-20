from __future__ import absolute_import, unicode_literals
import netsvc
import os
from six import string_types
from osv import osv, fields
import pooler
import re
import time
from tools.translate import _
from tools.config import config
import tools
from oorq.decorators import job
import six
import json

LOGGER = netsvc.Logger()

class PowersmsSMSbox(osv.osv):
    _name = "powersms.smsbox"
    _description = 'Power SMS SMSbox included all type inbox,outbox,junk..'
    _rec_name = "reference"
    _order = "date_sms desc"

    callbacks = {'create': 'powersms_create_callback',
                 'write': 'powersms_write_callback',
                 'unlink': 'powersms_unlink_callback',
                }

    def powersms_callback(self, cursor, uid, ids, func, vals=None, context=None):
        """Crida el callback callbacks[func] del reference de ids
        """
        if context is None:
            context = {}
        data = self.read(cursor, uid, ids, ['reference', 'meta'])
        if not isinstance(data, list):
            data = [data]
        ids_cbk = {}
        ctx = context.copy()
        ctx['ps_callback_origin_ids'] = {}
        ctx['meta'] = {}
        if vals:
            init_meta = vals.get('meta', {}) or {}
            if isinstance(init_meta, string_types):
                init_meta = json.loads(init_meta)
        else:
            init_meta = {}
        for i in data:
            if not i['reference']:
                continue
            meta_vals = i['meta']
            if meta_vals:
                meta = json.loads(meta_vals)
                meta.update(init_meta)
            else:
                meta = {}

            ref = i['reference'].split(',')
            ids_cbk[ref[0]] = ids_cbk.get(ref[0], []) + [int(ref[1])]
            ctx['ps_callback_origin_ids'][int(ref[1])] = i['id']
            ctx['meta'][int(ref[1])] = meta
        for model in ids_cbk:
            src = self.pool.get(model)
            try:
                if vals:
                    getattr(src, self.callbacks[func])(cursor, uid,
                                                ids_cbk[model], vals, ctx)
                else:
                    getattr(src, self.callbacks[func])(cursor, uid,
                                                ids_cbk[model], ctx)
            except AttributeError:
                pass

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}
        src_id = context.get('src_rec_id', False)
        if src_id:
            upd_vals = {
                'reference': '%s,%d' % (context['src_model'], src_id)
            }
            meta = context.get('meta')
            if meta:
                upd_vals['meta'] = json.dumps(context['meta'])
            vals.update(upd_vals)
        ps_id = super(PowersmsSMSbox,
                      self).create(cursor, uid, vals, context)
        self.powersms_callback(cursor, uid, ps_id, 'create', vals, context)
        return ps_id

    def validate_referenced_object_exists(self, cursor, uid, id, vals, context=None):
        ret = True
        fields = ['reference']
        result = self._read_flat(cursor, uid, id, fields, context, '_classic_read')
        for r in result:
            if 'reference' in r.keys():
                v = r['reference']
                if v:
                    model, ref_id = v.split(',')
                    ref_obj = self.pool.get(model)

                    if ref_id != '0':
                        id_exist = ref_obj.search(cursor, 1, [
                            ('id', '=', ref_id)
                        ], context={'active_test': False})
                        if not id_exist:
                            ret = False
        return ret

    def read(self, cursor, uid, ids, fields=None, context=None, load='_classic_read'):
        if context is None:
            context = {}
        select = ids
        if isinstance(ids, six.integer_types):
            select = [ids]
        valid_select = []
        for id in select:
            res = self.validate_referenced_object_exists(cursor, uid, [id], fields, context=None)
            if res:
                valid_select.append(id)
            else:
                super(PowersmsSMSbox,
                        self).unlink(cursor, uid, [id], context)
        ret = []
        if valid_select:
            ret = super(PowersmsSMSbox,
                        self).read(cursor, uid, valid_select, fields, context, load)
        if isinstance(ids, six.integer_types) and ret:
            return ret[0]
        return ret

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        meta = context.get('meta')
        if meta:
            vals['meta'] = json.dumps(meta)
        self.powersms_callback(cursor, uid, ids, 'write', vals, context)
        ret = super(PowersmsSMSbox,
                     self).write(cursor, uid, ids, vals, context)
        return ret

    def unlink(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        self.powersms_callback(cursor, uid, ids, 'unlink', context=context)
        ret = super(PowersmsSMSbox,
                     self).unlink(cursor, uid, ids, context)
        return ret

    def _get_models(self, cursor, uid, context={}):
        cursor.execute('select m.model, m.name from ir_model m order by m.model')
        return cursor.fetchall()

    def run_sms_scheduler(self, cursor, user, context=None):
        """
        This method is called by Open ERP Scheduler
        to periodically fetch sms
        """
        try:
            self.send_all_sms(cursor, user, context=context)
        except Exception as e:
            LOGGER.notifyChannel(
                                 _("Power SMS"),
                                 netsvc.LOG_ERROR,
                                 _("Error sending sms: %s") % str(e))

    def send_all_sms(self, cr, uid, ids=None, context=None):
        if ids is None:
            ids = []
        if context is None:
            context = {}
        #8888888888888 SENDS SMS IN OUTBOX 8888888888888888888#
        #get ids of smss in outbox
        filters = [('folder', '=', 'outbox'), ('state', '!=', 'sending')]
        if 'filters' in context.keys():
            for each_filter in context['filters']:
                filters.append(each_filter)
        limit = context.get('limit', None)
        order = "date_sms desc"
        ids = self.search(cr, uid, filters,
                          limit=limit, order=order,
                          context=context)
        LOGGER.notifyChannel('Power SMS', netsvc.LOG_INFO,
                             'Sending All SMS (PID: %s)' % os.getpid())
        # To prevent resend the same sms in several send_all_sms() calls
        # We put this in a new cursor/transaction to avoid concurrent
        # transaction isolation problems
        db = pooler.get_db_only(cr.dbname)
        cr_tmp = db.cursor()
        try:
            self.write(cr_tmp, uid, ids, {'state':'sending'}, context)
            cr_tmp.commit()
        except:
            cr_tmp.rollback()
        finally:
            cr_tmp.close()
        #send sms one by one
        if ids:
            self.async_send_this_sms(cr, uid, ids, context)
        return True

    @job(queue='powersms', timeout=180)
    def async_send_this_sms(self, cr, uid, ids=None, context=None):
        self.send_this_sms(cr, uid, ids, context)

    def _get_attatchment_payload(self, cursor, uid, attachment_ids, context=None):
        if not attachment_ids:
            return {}

        if not isinstance(attachment_ids, (tuple, list)):
            attachment_ids = [attachment_ids]

        attc_obj = self.pool.get('ir.attachment')
        return {
            attc['datas_fname']: attc['datas']
            for attc in attc_obj.read(cursor, uid, attachment_ids, ['datas_fname', 'datas'], context=context)
        }

    def send_this_sms(self, cr, uid, ids=None, context=None):
        if ids is None:
            ids = []
        #8888888888888 SENDS THIS SMS IN OUTBOX 8888888888888888888#
        #send sms one by one
        if not context:
            context = {}
        core_obj = self.pool.get('powersms.core_accounts')
        for id in ids:
            try:
                values = self.read(cr, uid, id, [], context) #Values will be a dictionary of all entries in the record ref by id
                # ids, from_name, numbers_to, body = '', payload = None, context = None

                result = core_obj.send_sms(
                    cr, uid, [values['psms_account_id'][0]],
                    values.get('psms_from', '') or '',
                    values.get('psms_to', '') or '',
                    values.get('psms_body_text', '') or '',
                    self._get_attatchment_payload(cr, uid, values.get('pem_attachments_ids'), context=context),
                    # todo payload pem_attachments_ids read
                    context=context
                )
                if result is True:
                    self.write(cr, uid, id, {'folder':'sent', 'state':'sent', 'date_sms':time.strftime("%Y-%m-%d %H:%M:%S")}, context)
                    self.historise(cr, uid, [id], "SMS sent successfully", context)
                else:
                    self.historise(cr, uid, [id], result, context, error=True)
                    self.write(cr, uid, id, {'state':'na'}, context)
            except Exception as error:
                logger = netsvc.Logger()
                logger.notifyChannel(_("Power SMS"), netsvc.LOG_ERROR, _("Sending of SMS %s failed. Probable Reason: Could not login to server\nError: %s") % (id, error))
                self.historise(cr, uid, [id], error, context, error=True)
                self.write(cr, uid, id, {'state':'na'}, context)
        return True

    def historise(self, cr, uid, ids, message='', context=None, error=False):
        user_obj = self.pool.get('res.users')
        if not context:
            context = {}
        user = user_obj.browse(cr, uid, uid)
        if 'lang' not in context:
            context.update({'lang': user.context_lang})
        for psms_id in ids:
            history = self.read(
                cr, uid, psms_id, ['history'], context).get('history', '') or ''
            history_limit = config.get('psms_history_limit', 10)
            # Limit history to X lines, then rotate
            if len(history.split('\n')) > history_limit:
                history = '\n'.join(history.split('\n')[1:])
            history_newline = "\n{}: {}".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), tools.ustr(message)
            )
            smsbox_wv = {'history': (history or '') + history_newline}
            if error:
                smsbox_wv.update({'folder': 'error', 'state': 'na'})
            self.write(cr, uid, psms_id, smsbox_wv, context=context)

    def check_mobile(self, mobile_number):
        if not re.match(r"((?:\+34)*|(?:0034)*)6[0-9]{8}|((?:\+34)*|(?:0034)*)7[0-9]{8}", mobile_number):
            return False
        return True

    def is_valid(self, cursor, uid, sms_id, context=None):
        sms = self.read(cursor, uid, sms_id, ['psms_to'], context)
        return self.check_mobile(sms['psms_to'])

    _columns = {
            'psms_account_id' :fields.many2one(
                            'powersms.core_accounts',
                            'User account',
                            required=True),
            'psms_from':fields.char(
                            'From',
                            size=64),
            'date_sms':fields.datetime(
                            'Rec/Sent Date'),
            'psms_to':fields.char(
                            'Recepient (To)',
                            size=250,),
            'psms_body_text':fields.text(
                            'Standard Body (Text)'),
            'state':fields.selection([
                            ('read', 'Read'),
                            ('unread', 'Un-Read'),
                            ('na', 'Not Applicable'),
                            ('sending', 'Sending'),
                            ('sent', 'Sent'),
                            ], 'Status', required=True),
            'folder':fields.selection([
                            ('inbox', 'Inbox'),
                            ('drafts', 'Drafts'),
                            ('outbox', 'Outbox'),
                            ('trash', 'Trash'),
                            ('followup', 'Follow Up'),
                            ('sent', 'Sent Items'),
                            ('error', 'Error'),
                            ], 'Folder', required=True),
            'history':fields.text(
                            'History',
                            readonly=True,
                            store=True),
            'reference': fields.reference('Source Object', selection=_get_models,
                                        size=128),
            'meta': fields.text('Meta information'),
            'pem_attachments_ids': fields.many2many(
                'ir.attachment',
                'sms_attachments_rel',
                'sms_id', 'att_id',
                'Attachments'
            ),
        }

    _defaults = {
        'state': lambda * a: 'na',
        'folder': lambda * a: 'outbox',
    }

PowersmsSMSbox()
