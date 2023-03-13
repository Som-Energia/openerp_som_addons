# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from osv import osv
from osv import fields


class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def _www_current_pagament(self, cursor, uid, ids, field_name, arg,
                              context=None):
        if not isinstance(ids, (list, set, tuple)):
            ids = [ids]
        res = dict.fromkeys(ids, True)
        factura_obj = self.pool.get('giscedata.facturacio.factura')
        conf_obj = self.pool.get('res.config')
        interval_venciment = int(conf_obj.get(
            cursor, uid, 'www_interval_venciment', '10'))
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for polissa_id in ids:
            search = [('state', '=', 'open'),
                      ('polissa_id', '=', polissa_id),
                      ('type', 'like', 'out\_')]
            invoices_open = factura_obj.search(cursor, uid, search)
            if invoices_open:
                invoices = factura_obj.read(
                    cursor, uid, invoices_open, ['date_invoice'])
                for invoice in invoices:
                    date_invoice = datetime.strptime(
                        invoice['date_invoice'], '%Y-%m-%d') + timedelta(
                        days=interval_venciment)
                    if date_invoice < now:
                        res[polissa_id] = False
        return res

    def _www_get_comptador_id(self, cursor, uid, polissa_id, comptador_name):
        comptador_obj = self.pool.get('giscedata.lectures.comptador')
        comptador_id = False
        if comptador_name:
            search_params = [('polissa.id', '=', polissa_id),
                             ('name', '=', comptador_name)]
            comptador_id = comptador_obj.search(
                cursor, uid, search_params, 0, 0, False, {'active_test': False})
            if comptador_id:
                comptador_id = comptador_id[0]
        return comptador_id

    def www_ultimes_lectures_reals(self, cursor, uid, ids):
        lectures = []
        if isinstance(ids, (list, set, tuple)):
            polissa_id = ids[0]
        else:
            polissa_id = ids
        conf_obj = self.pool.get('res.config')
        pool_lect_obj = self.pool.get('giscedata.lectures.lectura.pool')
        polissa_obj = self.pool.get('giscedata.polissa')
        lect_origen_obj = self.pool.get('giscedata.lectures.origen')
        comptador_obj = self.pool.get('giscedata.lectures.comptador')

        # Eliminat codi 40 del filtre, ara retorna també estimades
        search_params = [('codi', 'not in', ['99'])]
        origen_ids = lect_origen_obj.search(cursor, uid, search_params)
        comptador_name = polissa_obj.read(
            cursor, uid, polissa_id, ['comptador'])
        comptador_id = self._www_get_comptador_id(
            cursor, uid, polissa_id, comptador_name['comptador'])

        if not comptador_name['comptador']:
            search_params = [('polissa.id', '=', polissa_id)]
            llista_comptadors = comptador_obj.search(
                cursor, uid, search_params, 0, 0, False, {'active_test': False})
            llista_comptadors.sort(reverse=True)
            comptador_name = comptador_obj.read(
                cursor, uid, llista_comptadors[0], ['name'])
            comptador_id = self._www_get_comptador_id(
                cursor, uid, polissa_id, comptador_name['name'])

        if not comptador_id:
            return lectures

        search_params = [('comptador.id', '=', comptador_id),
                         ('origen_id', 'in', origen_ids),
                         ('tipus', '=', 'A')]
        limit_lectures = int(conf_obj.get(
            cursor, uid, 'www_limit_lectures', '5'))
        lect_ids = pool_lect_obj.search(
            cursor, uid, search_params, 0, limit_lectures, 'name desc', {'active_test': False})
        read_fields = ['name', 'periode', 'lectura', 'origen_id']
        for lectura in pool_lect_obj.read(cursor, uid, lect_ids, read_fields):
            data = datetime.strptime(lectura['name'], '%Y-%m-%d')
            origen_code = lect_origen_obj.read(
                cursor, uid, lectura['origen_id'][0], ['codi']
            )['codi']

            if origen_code in ('50',):
                origen = 'Autolectura'
            elif origen_code in ('40',):
                origen = 'Distribuidora (Estimada)'
            else:
                origen = 'Distribuidora (Real)'
            lectures.append({'data': data.strftime('%d-%m-%Y'),
                             'periode': lectura['periode'][1],
                             'lectura': lectura['lectura'],
                             'origen': origen
                             })
        return lectures

    _columns = {
        'www_current_pagament': fields.function(_www_current_pagament,
                                                string='Pagament corrent portal',
                                                type='boolean', method=True),
    }


GiscedataPolissa()
