# -*- coding: utf-8 -*-
from osv import osv


class ProductPricelistVersion(osv.osv):
    _name = 'product.pricelist.version'
    _inherit = 'product.pricelist.version'

    def _dates_overlap(self, version, date_start, date_end):
        version_start = version.date_start or ''
        version_end = version.date_end or '9999-12-31'
        wanted_start = date_start or ''
        wanted_end = date_end or '9999-12-31'
        return version_end >= wanted_start and version_start <= wanted_end

    def ensure_demo_tarifas_electricidad_version(self, cr, uid, context=None):
        if context is None:
            context = {}

        imd_obj = self.pool.get('ir.model.data')
        pricelist_id = imd_obj.get_object_reference(
            cr, uid, 'giscedata_facturacio', 'pricelist_tarifas_electricidad'
        )[1]
        values = {
            'pricelist_id': pricelist_id,
            'name': 'Versio 1',
            'date_start': '2021-01-01',
            'date_end': False,
        }
        xml_id = 'product_pricelist_version_tarifas_electridad'
        xml_version_id = False

        try:
            xml_version_id = imd_obj.get_object_reference(
                cr, uid, 'som_polissa_condicions_generals', xml_id
            )[1]
        except ValueError:
            pass

        if xml_version_id:
            xml_version_ids = self.search(
                cr, uid, [('id', '=', xml_version_id)], context=context
            )
            if xml_version_ids:
                return imd_obj._update(
                    cr, uid, self._name, 'som_polissa_condicions_generals', values,
                    xml_id=xml_id, res_id=xml_version_id,
                    noupdate=False, mode='init', context=context
                )
            stale_imd_id = imd_obj._get_id(
                cr, uid, 'som_polissa_condicions_generals', xml_id
            )
            if stale_imd_id:
                imd_obj.unlink(cr, uid, [stale_imd_id], context=context)

        version_ids = self.search(
            cr, uid, [('pricelist_id', '=', pricelist_id), ('active', '=', True)], context=context
        )
        for version in self.browse(cr, uid, version_ids, context=context):
            if self._dates_overlap(version, values['date_start'], values['date_end']):
                imd_obj._update(
                    cr, uid, self._name, 'som_polissa_condicions_generals', {},
                    xml_id=xml_id, res_id=version.id,
                    noupdate=False, mode='init', context=context
                )
                return version.id

        return imd_obj._update(
            cr, uid, self._name, 'som_polissa_condicions_generals', values,
            xml_id=xml_id, noupdate=False,
            mode='init', context=context
        )


ProductPricelistVersion()
