from osv import osv
from datetime import date, timedelta
from oorq.oorq import AsyncMode
from som_polissa.exceptions import exceptions
import logging


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
                try:
                    new_modcon_vals = {
                        "llista_preu": pol_obj.mapping_tarifa_no_social(cursor, uid, modcon['polissa_id'][0])  # noqa: E501,
                    }
                    polissa = pol_obj.browse(cursor, uid, modcon['polissa_id'][0], context=context)
                    polissa.send_signal("modcontractual")
                    pol_obj.write(cursor, uid, polissa.id, new_modcon_vals, context=context)

                    wz_crear_mc_obj = self.pool.get("giscedata.polissa.crear.contracte")
                    ctx = {"active_id": polissa.id}
                    params = {
                        "duracio": "nou",
                        "accio": "nou",
                    }
                    wiz_id = wz_crear_mc_obj.create(cursor, uid, params, context=ctx)
                    wiz = wz_crear_mc_obj.browse(cursor, uid, [wiz_id])[0]
                    data_activacio = date.today() + timedelta(days=1)
                    res = wz_crear_mc_obj.onchange_duracio(
                        cursor, uid, [wiz.id], str(data_activacio), wiz.duracio, context=ctx
                    )
                    if res.get("warning", False):
                        polissa.send_signal("undo_modcontractual")
                        raise osv.except_osv("Error", res["warning"])
                    else:
                        wiz.write(
                            {
                                "data_inici": str(data_activacio),
                                "data_final": str(data_activacio + timedelta(days=364)),
                            }
                        )

                        with AsyncMode("sync"):
                            wiz.action_crear_contracte()

                    social_tariff_modcons_ids.append(modcon['id'])
                except Exception as e:
                    polissa.send_signal("undo_modcontractual")
                    logger = logging.getLogger('openerp.crontab.update_invoices')
                    logger.error('Error creating non-social tariff modcontractual for polissa id {}: {}'.format(modcon['polissa_id'][0], str(e)))  # noqa: E501
                    raise exceptions.UnexpectedException()

        if social_tariff_ids:
            # remove social tariff ids form ids
            ids = [modcon_id for modcon_id in ids if modcon_id not in social_tariff_modcons_ids]

        return super(GiscedataPolissaModcontractual, self).renovar(cursor, uid, ids, context=context)  # noqa: E501


GiscedataPolissaModcontractual()
