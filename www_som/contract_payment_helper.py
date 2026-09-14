# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv
from som_polissa.exceptions import exceptions
from www_som.helpers import www_entry_point


class SomContractPaymentHelper(osv.osv_memory):
    _name = "som.contract.payment.helper"

    @www_entry_point(expected_exceptions=exceptions.SomPolissaException)
    def convert_to_recurring_card(self, cursor, uid, polissa_id, card_data, context=None):
        return self.pool.get("giscedata.polissa").convert_to_recurring_card(
            cursor, uid, polissa_id, card_data, context=(context or {}).copy()
        )


SomContractPaymentHelper()
