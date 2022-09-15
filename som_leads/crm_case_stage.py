from osv import osv, fields


class crm_case_stage(osv.osv):
    _name = 'crm.case.stage'
    _inherit = 'crm.case.stage'

    _columns = {
        'method': fields.char('Method Name', size=64),
    }

crm_case_stage()