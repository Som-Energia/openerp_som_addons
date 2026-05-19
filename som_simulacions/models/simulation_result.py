# # -*- coding: utf-8 -*-
# from osv import osv, fields


# class SomSimulacioResult(osv.osv):
#     _name = 'som.simulacio.result'
#     _description = 'Indexed estimate simulation result'

#     _columns = {
#         'name': fields.char('Reference', size=64, required=True),
#         'request_id': fields.many2one(
#             'som.simulacio.request', 'Request', required=True, ondelete='cascade'
#         ),
#         'untaxed_total': fields.float('Untaxed monthly total', digits=(16, 6)),
#         'selected_energy_price_id': fields.many2one(
#             'som.simulacio.energy.price.monthly', 'Selected monthly price', ondelete='set null'
#         ),
#         'selected_coeff_set_id': fields.many2one(
#             'som.simulacio.annual.coeff', 'Selected coefficient set', ondelete='set null'
#         ),
#         'fallback_flags': fields.text('Fallback usage flags'),
#         'traceability_payload': fields.text('Traceability payload'),
#         'line_ids': fields.one2many(
#             'som.simulacio.result.line', 'result_id', 'Result lines'
#         ),
#     }


# SomSimulacioResult()
