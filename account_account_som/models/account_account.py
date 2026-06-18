# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import fields, osv


class AccountAccount(osv.osv):
    """Modifiquem account_account per poder mostrat-lo o no al llistat a voluntat"""

    _name = "account.account"
    _inherit = "account.account"

    _columns = {"ocultar": fields.boolean("Ocultar compte")}

    _defaults = {
        "ocultar": lambda *a: False,
    }


AccountAccount()
