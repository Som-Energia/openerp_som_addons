# -*- coding: utf-8 -*-
from osv import osv


class WizardCreateDistributionAgreement(osv.osv_memory):

    _name = 'wizard.create.distribution.agreement'

    # TODO
    def create_distribution_agreement_txt(self, cursor, uid, context=None):
        if context is None:
            context = {}

        current_gurb = context.get('active_id')
        if not current_gurb:
            return False

        gurb_cups_o = self.pool.get('som.gurb.cups')

        search_params = [
            ('gurb_id', '=', current_gurb),
        ]

        som_gurb_cups_ids = gurb_cups_o.search(
            cursor, uid, search_params, context=context
        )

        return som_gurb_cups_ids


WizardCreateDistributionAgreement()
