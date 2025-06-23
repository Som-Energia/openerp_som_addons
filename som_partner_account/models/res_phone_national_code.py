# -*- coding: utf-8 -*-

from osv import fields, osv


class ResPhoneNationalCode(osv.osv):
    """Afegim el codi nacional de telèfon a la taula res.partner.address"""

    _name = "res.phone.national.code"

    _columns = {
        'name': fields.char(
            'Nom', required=True, help='Nom descriptiu del codi nacional de telèfon'),
        'code': fields.char('Codi nacional de telèfon'),
        'country_id': fields.many2one('res.country', 'País', required=True, ondelete='cascade'),
        'active': fields.boolean(
            'Actiu', help='Si està inactiu, no es mostrarà en els formularis de telèfons'),
        'sequence': fields.integer(
            'Seqüència', help='Ordre de visualització dels codis nacionals de telèfon'),
        'phone_number_format': fields.char('Format del número de telèfon'),
        'phone_number_example': fields.char('Exemple de número de telèfon'),
    }


ResPhoneNationalCode()
