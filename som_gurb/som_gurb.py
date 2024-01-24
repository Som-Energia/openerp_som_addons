# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomGurb(osv.osv):
    _name = "som.gurb"
    _description = _('Grup generació urbana')

    # TODO: Add constrains and requireds
    _columns = {
        'name': fields.char('Nom GURB', size=60, required=True),
        'code': fields.char('Codi GURB', size=60, required=True),
        'roof_owner': fields.many2one("res.partner", 'Propietari teulada', required=True),
        'type': fields.selection(
            [("type1", "Tipus 1"), ("type2", "Tipus 2"), ],  # TODO: Types
            "Tipus agrupació",
            required=True,
        ),
        'logo': fields.boolean('Logo'),
        'address': fields.many2one('res.partner.address', 'Adreça', required=True),
        'province': fields.char('Provincia', size=60, readonly=True),
        'zip_code': fields.char('Codi postal', size=60, readonly=True),
        'sig_data': fields.char('Dades SIG', size=60, required=True),
        'activation_date': fields.date(u"Data activació GURB", required=True),
        'state': fields.selection(
            [("state1", "Estat 1"), ("state2", "Estat 2"), ],  # TODO: States
            "Estat GURB",
            required=True,
        ),
        'joining_fee': fields.float('Tarifa cost adhesió'),  # TODO: New model
        'service_fee': fields.float('Tarifa quota servei'),  # TODO: New model
        'max_power': fields.float('Topall max. per contracte (kW)'),
        'mix_power': fields.float('Topall mix. per contracte (kW)'),
        'critical_incomplete_state': fields.integer('Estat crític incomplet (%)'),
        'first_opening_days': fields.integer('Dies primera obertura'),
        'reopening_days': fields.integer('Dies reobertura'),
        'notes': fields.text('Observacions'),
        'history_box': fields.text('Històric del GURB', readonly=True),
        # TODO: Autoconsum, betes and registrador
    }

    defaults = {
        'logo': lambda *a: False,
        'state': lambda *a: 'state1',
    }


SomGurb()
