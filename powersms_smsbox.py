import netsvc
import os
from osv import osv, fields
import pooler
import re
import time
from tools.translate import _
from tools.config import config
import tools

LOGGER = netsvc.Logger()

class PowersmsSMSbox(osv.osv):
    _name = "powersms.smsbox"
    _description = 'Power SMS SMSbox included all type inbox,outbox,junk..'
    _rec_name = "psms_subject"
    _order = "date_sms desc"

    def run_sms_scheduler(self, cursor, user, context=None):
        """
        This method is called by Open ERP Scheduler
        to periodically fetch sms
        """
        #import pudb;pu.db
        try:
            self.send_all_sms(cursor, user, context=context)
        except Exception, e:
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
        self.send_this_sms(cr, uid, ids, context)
        return True

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
                result = core_obj.send_sms(
                    cr, uid, [values['psms_account_id'][0]],
                    values.get('psms_from', u'') or u'',
                    values.get('psms_to', u'') or u'',
                    values.get('psms_body_text', u'') or u'',
                    context=context
                )
                if result == True:
                    self.write(cr, uid, id, {'folder':'sent', 'state':'sent', 'date_sms':time.strftime("%Y-%m-%d %H:%M:%S")}, context)
                    self.historise(cr, uid, [id], "SMS sent successfully", context)
                else:
                    self.historise(cr, uid, [id], result, context, error=True)
            except Exception, error:
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
            # Notify the sender errors
            if context.get('notify_errors', False) \
                    and not context.get('bounce', False) \
                    and error:
                sms = self.browse(cr, uid, psms_id)
                vals = {
                    'folder': 'outbox',
                    'history': '',
                    'pem_to': sms.pem_account_id.email_id,
                    'pem_subject': _(
                        u"Error sending email with id {}"
                    ).format(sms.id)
                }
                bounce_sms_id = self.copy(cr, uid, psms_id, vals)
                ctx = context.copy()
                ctx.update({'bounce': True})
                self.send_this_sms(cr, uid, [bounce_sms_id], ctx)
                bounce_sms = self.browse(cr, uid, bounce_sms_id)
                # If bounce sms cannot be sent, unlink it
                if bounce_sms.folder != 'sent':
                    bounce_sms.unlink()
            history = self.read(
                cr, uid, psms_id, ['history'], context).get('history', '') or ''
            history_limit = config.get('psms_history_limit', 10)
            # Limit history to X lines, then rotate
            if len(history.split('\n')) > history_limit:
                history = '\n'.join(history.split('\n')[1:])
            history_newline = "\n{}: {}".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), tools.ustr(message)
            )
            self.write(
                cr, uid, psms_id, {
                    'history': (history or '') + history_newline}, context)

    def check_mobile(self, mobile_number):
        if not re.match(r"((?:\+34)*|(?:0034)*)6[0-9]{8}|((?:\+34)*|(?:0034)*)7[0-9]{8}", mobile_number):
            return False
        return True

    def is_valid(self, cursor, uid, sms_id, context=None):
        mail = self.read(cursor, uid, sms_id, ['psms_to'], context)
        return self.check_mobile(mail['psms_to'])

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
                            ], 'Folder', required=True),
            'history':fields.text(
                            'History',
                            readonly=True,
                            store=True),
        }

    _defaults = {
        'state': lambda * a: 'na',
        'folder': lambda * a: 'outbox',
    }

PowersmsSMSbox()
