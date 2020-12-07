from osv import osv, fields
from tools.translate import _

class PowersmsCoreAccounts(osv.osv):
    """
    Object to store email account settings
    """
    _name = "powersms.core_accounts"

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