# -*- coding: utf-8 -*-
from osv import osv


class GiscedataSwitchingHelpers(osv.osv):

    _name = "giscedata.switching.helpers"
    _inherit = "giscedata.switching.helpers"

    def unsubscribe_extra_mailchimp_lists_hook(self, cursor, uid, titular_id, context=None):
        context = context or {}

        imd_obj = self.pool.get("ir.model.data")
        address_obj = self.pool.get("res.partner.address")
        polissa_obj = self.pool.get("giscedata.polissa")

        super(GiscedataSwitchingHelpers, self).unsubscribe_extra_mailchimp_lists_hook(
            cursor, uid, titular_id, context=context
        )

        ct_ss_partner_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_soci_ct'
        )[1]
        has_polissa_with_ctss = bool(polissa_obj.search(
            cursor,
            uid,
            [
                ("titular", "=", titular_id),
                ("soci", "=", ct_ss_partner_id),
            ],
            context={'active_test': False},
        ))

        if has_polissa_with_ctss:
            address_obj.unsubscribe_titular_in_ctss_lists(
                cursor, uid, titular_id, context=context
            )


GiscedataSwitchingHelpers()
