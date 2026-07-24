from osv import osv


class GiscedataCrmLead(osv.OsvInherits):
    _inherit = "giscedata.crm.lead"

    def get_lead_report(self, cursor, uid, lead_id, context=None):
        if context is None:
            context = {}
        imd_obj = self.pool.get('ir.model.data')
        report_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_condicions_generals', 'lead_contract_summary_full_report'
        )[1]
        return report_id


GiscedataCrmLead()
