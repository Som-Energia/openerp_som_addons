from osv import osv

class GiscedataCrmLead(osv.OsvInherits):

    _inherit = "giscedata.crm.lead"

    def contract_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        context['lead'] = True

        super(GiscedataCrmLead, self).contract_pdf(cursor, uid, ids, context=context)

GiscedataCrmLead()