# -*- coding: utf-8 -*-

from osv import osv


class GiscedataSwitchingHelpers(osv.osv):

    _name = 'giscedata.switching.helpers'
    _inherit = 'giscedata.switching.helpers'

    def activa_polissa_from_cn(self, cursor, uid, sw_id, context=None):
        res = super(GiscedataSwitchingHelpers, self).activa_polissa_from_cn(
            cursor, uid, sw_id, context=context)

        sw = self.pool.get("giscedata.switching").browse(cursor, uid, sw_id, context=context)
        # Si fa falta, activem el ov_user. Aixo enviara un mail al client amb la alta a la OV
        partner_address_obj = self.pool.get('res.partner.address')
        soci_obj = self.pool.get('somenergia.soci')
        partner_id = sw.cups_polissa_id.titular.id
        is_soci = soci_obj.search(cursor, uid, [('partner_id', '=', partner_id)], context=context)
        if is_soci:
            partner_address_obj.update_members_data_mailchimp_async(
                cursor, uid, [partner_id], context=context)
        else:
            partner_address_obj.subscribe_partner_in_customers_no_members_lists(
                cursor, uid, [partner_id], context=context)

        return res


GiscedataSwitchingHelpers()
