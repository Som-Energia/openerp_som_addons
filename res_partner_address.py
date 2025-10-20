from osv import osv
from som_polissa_soci.models.res_partner_address import FIELDS_SOCIS


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
    
    def fill_merge_fields_soci(self, cursor, uid, id, context=None):
        mailchimp_member = super(ResPartnerAddress, self).fill_merge_fields_soci(
            cursor, uid, id, context=context)

        soci_data = self._get_contract_data(cursor, uid, id, context=context)
        mailchimp_member["merge_fields"].update(
            {
                FIELDS_SOCIS["Generation"]: soci_data['generationkwh'], #  True or False            }
            }
        )

        return mailchimp_member

ResPartnerAddress()