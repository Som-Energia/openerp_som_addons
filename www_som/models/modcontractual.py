from osv import osv
from datetime import date, timedelta


class GiscedataPolissaModcontractual(osv.osv):
    _inherit = 'giscedata.polissa.modcontractual'

    def renovar(self, cursor, uid, ids, context=None):
        pol_obj = self.pool.get('giscedata.polissa')

        social_tariff_ids = pol_obj.mapping_tarifa_social(cursor, uid).values()
        social_tariff_modcons_ids = []
        for modcon in self.read(cursor, uid, ids, ['llista_preu', 'polissa_id'], context=context):
            if (modcon.get('llista_preu', [])
                    and modcon.get('llista_preu', [])[0] in social_tariff_ids):

                # TODO: Create new pending modcontractual without social tariff
                tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
                pol_vals = {
                    "llista_preu": pol_obj.mapping_tarifa_no_social(cursor, uid, modcon['polissa_id'][0])  # noqa: E501
                }
                pol_obj.create_contracte(
                    cursor, uid, modcon['polissa_id'][0], data_inici=tomorrow,
                    pol_vals=pol_vals, duracio='actual', accio='M', context=context
                )
                social_tariff_modcons_ids.append(modcon['id'])

        if social_tariff_ids:
            # remove social tariff ids form ids
            ids = [modcon_id for modcon_id in ids if modcon_id not in social_tariff_modcons_ids]

        return super(GiscedataPolissaModcontractual, self).renovar(cursor, uid, ids, context=context)  # noqa: E501


GiscedataPolissaModcontractual()
