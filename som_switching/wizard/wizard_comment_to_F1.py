from osv import osv, fields
# -*- coding: utf-8 -*-
from tools.translate import _


class wizard_comment_to_F1(osv.osv_memory):


    _name = 'wizard.comment.to.F1'

    def add_comment_to_F1(self, cursor, uid, ids, context=None):

        wiz = self.browse(cursor, uid, ids[0], context=context)
        if not wiz.comment:
            return {}

        active_ids = context.get('active_ids')

        model = self.pool.get('giscedata.facturacio.importacio.linia')


        for inv_id in active_ids:
            old_comment = model.read(cursor, uid, inv_id, ['user_observations'])['user_observations']
            old_comment = old_comment if old_comment else ''
            new_comment = wiz.comment + "\n"
            model.write(cursor, uid, inv_id, {'user_observations': new_comment + old_comment })

        return {}


    _columns = {
        'comment': fields.text(_(u"Afegir observacions F1"), readonly=False),
    }

wizard_comment_to_F1()