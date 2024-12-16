# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardCreateStaffUsers(osv.osv_memory):

    _name = "wizard.create.staff.users"

    def _update_wizard_status(self, cursor, uid, ids, state, info=''):
        values = {
            'state': state,
            'info': info,
        }
        self.write(cursor, uid, ids, values)

    def _create_partner_and_address(self, cursor, uid, wizard_data):
        partner_obj = self.pool.get("res.partner")
        address_obj = self.pool.get("res.partner.address")

        partner_data = {
            'name': wizard_data.user_to_staff.name,
            'vat': self._validate_vat(cursor, uid, wizard_data.vat),
            'lang': 'ca_ES',
        }
        partner_id = partner_obj.create(cursor, uid, partner_data)

        address_data = {
            'name': wizard_data.user_to_staff.name,
            'email': wizard_data.email,
            'partner_id': partner_id,
            'street': 'Carrer Pic de Peguera, 9',
            'zip': '17002',
            'city': 'Girona',
            'state_id': 20,
        }
        address_id = address_obj.create(cursor, uid, address_data)

        return address_id

    def _validate_vat(self, cursor, uid, vat):
        partner_obj = self.pool.get("res.partner")
        if not partner_obj.is_vat(vat) or vat[:2] != 'ES':
            raise osv.except_osv('Error validant el VAT!', 'El VAT no és vàlid')
        return vat.upper()

    def action_create_staff_users(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        user_obj = self.pool.get("res.users")

        wizard_data = self.browse(cursor, uid, ids[0])
        user_id = wizard_data.user_to_staff.id

        if user_id:
            user = user_obj.browse(cursor, uid, user_id)
            if not user.read():
                self._update_wizard_status(cursor, uid, ids, 'done', 'No s\'ha trobat cap usuaria')
                return True

            if not user['address_id']:
                address_id = self._create_partner_and_address(cursor, uid, wizard_data)
                user_obj.write(cursor, uid, user_id, {'address_id': address_id})
                self._update_wizard_status(cursor, uid, ids, 'done', 'Usuaria staff creada')
                return True

            if user['address_id']:
                self._update_wizard_status(cursor, uid, ids, 'done', 'Aquesta usuaria ja és staff')
                return True

        self._update_wizard_status(cursor, uid, ids, 'done', 'No s\'ha trobat cap usuaria')
        return True

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info', size=4000),
        'email': fields.char('Email', size=100),
        'user_to_staff': fields.many2one('res.users', 'Usuaria', required=True),
        'vat': fields.char('VAT', size=20),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }


WizardCreateStaffUsers()
