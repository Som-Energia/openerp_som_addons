from osv import osv, fields
from tools.translate import _

class PowersmsCoreAccounts(osv.osv):
    """
    Object to store sms account settings
    """
    _name = "powersms.core_accounts"


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
                                                'res.users'
                                                ).read(
                                                        cursor,
                                                        user,
                                                        user,
                                                        ['name'],
                                                        context
                                                        )['name'],
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