from __future__ import absolute_import, unicode_literals
from osv import osv, fields
from tools.translate import _
import netsvc

class PowersmsCoreAccounts(osv.osv):
    """
    Object to store sms account settings
    """
    _name = "powersms.core_accounts"

    def check_numbers(self, cr, uid, ids, numbers):
        box_obj = self.pool.get('powersms.smsbox')
        if box_obj.check_mobile(numbers):
            return True
        return False

    def send_sms(self, cr, uid, ids, from_name, numbers_to, body='', payload=None, context=None):
        if context is None:
            context = {}
        if payload is None:
            payload = {}

        def payload_parser(_payload):
            from base64 import b64decode
            import tempfile
            import os
            file_paths = []
            for file_name in _payload.keys():
                # Decode b64 from raw base64 attachment and write it to a buffer
                extension = '.{}'.format(file_name.split('.')[-1])
                f_name = file_name.replace(extension, '')
                fd, path = tempfile.mkstemp(prefix=f_name, suffix=extension)
                os.write(fd, b64decode(_payload[file_name]))
                os.close(fd)
                file_paths.append(path)
            return file_paths

        logger = netsvc.Logger()

        # TODO
        # - Check if numbers_to is a list, for the current code calls numbers_to will be one but better
        # if we allow multiple numbers
        if not self.check_numbers(cr, uid, ids, numbers_to):
            raise Exception("Incorrect cell number: " + numbers_to)

        # Try to send the e-mail from each allowed account
        # Only one mail is sent
        # TODO
        # - Fix this logic, if for example we provide 3 accounts and first raise exception the other 2
        #   will not be tried
        for account_id in ids:
            account = self.browse(cr, uid, account_id, context)

            try:
                return bool(account.provider_id.send_sms(
                    account_id, from_name, numbers_to, body=body, files=payload_parser(payload), context=context
                ))
            except Exception as error:
                logger.notifyChannel(
                    _("Power SMS"), netsvc.LOG_ERROR,
                    _("Could not create SMS "
                      "from Account \"{account.name}\".\n"
                      "Description: {error}").format(**locals())
                )
                return error

    def do_approval(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'approved'}, context=context)

    def filter_send_sms(self, cr, uid, sms_str):
        if not sms_str:
            sms_str = ''
        response = ''
        for e in sms_str.split(','):
            if self.pool.get('powersms.smsbox').check_mobile(e.strip()):
                if response:
                    response += ','
                response += e
        return response

    _columns = {
        'name': fields.char('SMS Account name',
                        size=64, required=True,
                        readonly=True, select=True,
                        states={'draft':[('readonly', False)]}),
        'user':fields.many2one('res.users',
                        'Related User', required=True,
                        readonly=True, states={'draft':[('readonly', False)]}),
        'tel_id': fields.char('Telephone ID',
                        size=120, required=True,
                        readonly=True, states={'draft':[('readonly', False)]} ,
                        help="eg: +34666666666"),
        'api_server': fields.char('SMS API server',
                        size=120, required=True,
                        readonly=True, states={'draft':[('readonly', False)]},
                        help="Enter name of outgoing server, eg: api.lleida.net"),
        'api_uname': fields.char('SMS API user Name',
                        size=120, required=False,
                        readonly=True, states={'draft':[('readonly', False)]}),
        'api_pass': fields.char('SMS API password',
                        size=120, invisible=True,
                        required=False, readonly=True,
                        states={'draft':[('readonly', False)]}),
        'state': fields.selection([
                                  ('draft', 'Initiated'),
                                  ('suspended', 'Suspended'),
                                  ('approved', 'Approved')
                                  ],
                        'Account Status', required=True, readonly=True),
        'allowed_groups': fields.many2many(
                        'res.groups',
                        'account_group_rel', 'templ_id', 'group_id',
                        string="Allowed User Groups",
                        help="Only users from these groups will be " \
                        "allowed to send SMS from this ID."),
        'provider_id': fields.many2one('powersms.provider', 'SMS Provider')
    }

    _defaults = {
         'name':lambda self, cursor, user, context:self.pool.get(
            'res.users').read(cursor, user, user, ['name'], context)['name'],
         'state':lambda * a:'draft',
         'user':lambda self, cursor, user, context:user,
    }
    _sql_constraints = [
        (
         'name_uniq',
         'unique (name)',
         'Another account already exists with this Name!')
    ]

PowersmsCoreAccounts()
