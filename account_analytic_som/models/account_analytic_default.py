# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class AccountAnalyticDefault(osv.osv):
    _name = "account.analytic.default"
    _inherit = "account.analytic.default"

    @classmethod
    def domain_get(cls, **kwargs):
        domain = super(AccountAnalyticDefault, cls).domain_get(**kwargs)
        # An omitted product is unrestricted; an explicitly missing one is not.
        if "product_id" in kwargs and not kwargs["product_id"]:
            domain.append(("product_id", "=", False))
        return domain


AccountAnalyticDefault()
