from osv import osv, fields
from tools.translate import _
import netsvc
from lleida_net.sms import Client

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

    def send_sms_lleida(self, cr, uid, ids, number_to, message, from_name, context=None):
        if isinstance(ids, list):
            ids = ids[0]
        if not self.check_numbers(cr, uid, ids, number_to):
            raise Exception("Incorrect cell number: " + number_to)

        values = self.read(cr, uid, ids, ['api_uname', 'api_pass'])
        c = Client(user=str(values['api_uname']), password=str(values['api_pass']))
        headers = {'content-type': 'application/x-www-form-urlencoded', 'accept': 'application/json'}
        resposta = c.API.post(resource='',json={
            "sms": {
                "txt": message,
                "dst": {
                    "num": number_to,
                },
                "src": from_name,
            }
        }, headers=headers)
        return resposta.result['code'] == 200 and resposta.result['status'] == u'Success'

    def send_sms(self, cr, uid, ids, from_name, numbers_to, body='', context=None):
        if context is None:
            context = {}
        logger = netsvc.Logger()
        # Try to send the e-mail from each allowed account
        # Only one mail is sent
        for account_id in ids:
            account = self.browse(cr, uid, account_id, context)
            try:
                self.send_sms_lleida(cr, uid, ids, numbers_to, body, from_name)
                return True
            except Exception as error:
                logger.notifyChannel(
                    _("Power SMS"), netsvc.LOG_ERROR,
                    _("Could not create mail "
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
        'state':fields.selection([
                                  ('draft', 'Initiated'),
                                  ('suspended', 'Suspended'),
                                  ('approved', 'Approved')
                                  ],
                        'Account Status', required=True, readonly=True),
        'allowed_groups':fields.many2many(
                        'res.groups',
                        'account_group_rel', 'templ_id', 'group_id',
                        string="Allowed User Groups",
                        help="Only users from these groups will be " \
                        "allowed to send SMS from this ID."),
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
