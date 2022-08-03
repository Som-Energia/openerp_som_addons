# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime

class GiscedataAtcTag(osv.osv):
    _name = 'giscedata.atc.tag'

    _columns = {
        'name': fields.char(u"Etiqueta", size=100),
        'titol': fields.char(u"Títol", size=200),
        'description': fields.char(u"Descripció", size=300),
        'creation_date': fields.date(u"Data creació", required=True),
        'text_R1': fields.text(u'Proposta text R1'),
        'active': fields.boolean('Actiu'),
    }

    _defaults = {
        'active': lambda *a: True,
        'creation_date': lambda *a: datetime.today().strftime('%Y-%m-%d'),
    }

GiscedataAtcTag()

class GiscedataAtc(osv.osv):

    _inherit = 'giscedata.atc'

    def case_close_pre_hook(self, cursor, uid, ids, *args):
        if len(args):
            context = args[0]
        else:
            context = {}

        res = super(GiscedataAtc, self).case_close_pre_hook(cursor, uid, ids, *args)

        conf_obj = self.pool.get("res.config")
        treure = int(conf_obj.get(cursor, uid, "treure_facturacio_suspesa_on_cac_close", "0"))
        if treure:
            pol_ids = self.read(cursor, uid, ids, ['polissa_id'], context=context)
            pol_ids = [x['polissa_id'][0] for x in pol_ids]
            self.pool.get("giscedata.polissa").write(cursor, uid, pol_ids, {'facturacio_suspesa': False})
        return res

    def unlink(self, cursor, uid, ids, context=None):
        super(GiscedataAtc, self).case_cancel(cursor, uid, ids, context)

    _columns = {
        'tag': fields.many2one('giscedata.atc.tag', "Etiqueta"),
    }

GiscedataAtc()

