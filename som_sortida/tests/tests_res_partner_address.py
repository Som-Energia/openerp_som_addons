# -*- coding: utf-8 -*-
from destral import testing


class TestsPartnerAddress(testing.OOTestCaseWithCursor):
    def test_fill_merge_fields_titular_polissa_ctss(self):
        cursor = self.cursor
        uid = self.uid
        rpa_obj = self.pool.get("res.partner.address")
        self.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        res = rpa_obj.fill_merge_fields_titular_polissa_ctss(cursor, uid, polissa_id)

        self.maxDiff = None
        self.assertEqual(res, {
            'email_address': u'test@test.test',
            'merge_fields': {
                'EMAIL': u'test@test.test',
                'FNAME': u'Pere',
                'MMERGE11': u'08600',
                'MMERGE3': False,
                'MMERGE4': 'Origen vinculat al CT sense socia',
                'MMERGE5': u'S202129',
                'MMERGE6': 'Apadrinada',
                'MMERGE10': u'Catalu\xf1a',
                'MMERGE6': 'Apadrinada',
                'MMERGE7': u'Berga',
                'MMERGE8': u'Bergued\xe0',
                'MMERGE9': u'Barcelona'
            },
            'status': 'subscribed'
        })
