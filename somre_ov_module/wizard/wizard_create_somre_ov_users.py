# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardCreateSomreOvUsers(osv.osv_memory):

    """Classe per gestionar el canvi de contrasenya
    """

    _name = "wizard.create.somre.ov.users"

    def action_create_somre_ov_users(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        partner_id = self.read(cursor, uid, ids[0], ['partner_id'])[0]['partner_id']

        ov_users_obj = self.pool.get('somre.ov.users')
        ov_users_ids = ov_users_obj.search(cursor, uid, [
            ('partner_id', '=', partner_id)
        ], context={"active_test": False})

        if len(ov_users_ids) > 0:
            self.write(cursor, uid, ids, {
                'state': 'done',
                'info': u'El Client ja és usuari de la oficina virtual de representació!',
            })
            return False

        par_obj = self.pool.get('res.partner')
        par = par_obj.browse(cursor, uid, partner_id)
        ov_users_ids = ov_users_obj.search(cursor, uid, [
            ('vat', '=', par.vat)
        ], context={"active_test": False})

        if len(ov_users_ids) > 0:
            self.write(cursor, uid, ids, {
                'state': 'done',
                'info': u'Ja existeix un usuari amb aquest NIF!',
            })
            return False

        if len(par.address) == 0 or not par.address[0].email:
            self.write(cursor, uid, ids, {
                'state': 'done',
                'info': u'El Client no té correu electrónic definit',
            })
            return False

        ov_users_obj.create(cursor, uid, {'partner_id': partner_id})
        self.write(cursor, uid, ids, {
            'state': 'done',
            'info': u'Usuari de la oficina virtual de representació creat correctament',
        })
        return True

    _columns = {
        'state': fields.char('State', size=16),
        'partner_id': fields.many2one('res.partner', 'Client', required=True),
        'info': fields.text('Info', size=4000),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }


WizardCreateSomreOvUsers()
