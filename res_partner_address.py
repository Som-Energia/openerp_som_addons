from osv import osv


class ResPartnerAddress(osv.osv):
    _name = "res.partner.address"
    _inherit = "res.partner.address"

    def _get_contract_data(self, cursor, uid, partner_id, context):
        soci_data = super(ResPartnerAddress, self)._get_contract_data(
            cursor, uid, partner_id, context=context)

        # Generationkwh
        gen_obj = self.pool.get('generationkwh.investment')
        soc_obj = self.pool.get('somenergia.soci')
        soci_id = soc_obj.search([('partner_id','=',partner_id)])

        gen_data = gen_obj.search(cursor, uid, [('member_id','=',soci_id)])
        if gen_data:
            soci_data['generationkwh'] = True
        else:
            soci_data['generationkwh'] = False

        return soci_data
    
ResPartnerAddress()