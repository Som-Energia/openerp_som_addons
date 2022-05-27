# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime

from giscedata_switching_comer.giscedata_switching import POTENCIES_TRIFASIQUES


class GiscedataSwitchingAparell(osv.osv):

    _name = 'giscedata.switching.aparell'
    _inherit = "giscedata.switching.aparell"

    def calcula_lloguer_comptador(self, cursor, uid, ids, tarifaatr=None,
                                  potencia=None, context=None):
        '''En funció del tipus d'aparell, calcula el lloguer del comptador'''
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        irdata_obj = self.pool.get('ir.model.data')
        uom_obj = self.pool.get('product.uom')
        pm_obj = self.pool.get('giscedata.switching.pm')
        product_obj = self.pool.get('product.product')
        pricelist_obj = self.pool.get('product.pricelist')
        tarifa_obj = self.pool.get('giscedata.polissa.tarifa')

        # Tarifes electricitat
        tar_elec_data = irdata_obj._get_id(cursor, uid, 'giscedata_facturacio',
                                           'pricelist_tarifas_electricidad')

        tar_elec_id = irdata_obj.read(cursor, uid, tar_elec_data,
                                      ['res_id'])['res_id']

        # TODO: es podria tenir en compte any de traspas
        # Unitats de mesura ALQ/mes i ALQ/dia
        data_names = ['uom_aql_elec_dia', 'uom_aql_elec_mes']
        uom_alq_datas = irdata_obj.search(cursor, uid,
                                          [('model', '=', 'product.uom'),
                                           ('name', 'in', data_names)])

        uom_alq_ids = [p['res_id'] for p in
                       irdata_obj.read(cursor, uid, uom_alq_datas, ['res_id'])]

        uom_alq_vals = uom_obj.read(cursor, uid, uom_alq_ids, ['name'])

        uoms = dict([(u['name'], u['id']) for u in uom_alq_vals])

        #Productes de lloguer
        data_names = ['alq_cont_st_ea_mono_resto',
                      'alq_cont_st_ea_tri',
                      'alq_cont_dh_mono',
                      'alq_cont_dh_tri_doble',
                      'alq_conta_tele',
                      'alq_conta_tele_tri',
                      # 30 and AT fixed price (ALQ30)
                      'alq_cont_30_default',
                      ]

        alq_datas = irdata_obj.search(cursor, uid,
                                      [('model', '=', 'product.product'),
                                       ('name', 'in', data_names)])

        alq_ids = [p['res_id'] for p in
                   irdata_obj.read(cursor, uid, alq_datas, ['res_id'])]

        alq_vals = product_obj.read(cursor, uid, alq_ids, ['list_price',
                                                           'code', 'uom_id'])

        preus = dict([(a['code'], {'preu': a['list_price'],
                                   'uom': uoms['ALQ/mes'],
                                   'id': a['id']})
                      for a in alq_vals])

        # Dades de l'aparell
        aparell_vals = self.read(cursor, uid, ids, ['tipus_em', 'propietat',
                                                    'pm_id'])

        pm_vals = pm_obj.read(cursor, uid, aparell_vals['pm_id'][0],
                              ['mode_lectura', 'tensio_pm'])

        #DH segons Tarifa
        es_dh = False
        es_30 = False
        if tarifaatr:
            # 3.0 fare, fixed price
            if tarifaatr == '003':
                es_30 = True

            tar_id = tarifa_obj.get_tarifa_from_ocsum(cursor, uid, tarifaatr)

            if tar_id:
                es_dh = (tarifa_obj.get_num_periodes(cursor, uid,
                                                     [tar_id]) > 1)
            tar_vals = tarifa_obj.read(cursor, uid, tar_id, ['tipus'])
            if tar_vals['tipus'] == 'AT':
                es_30 = True

        #Telegestió?
        es_tg = pm_vals['mode_lectura'] == '4'

        #Trifàsic segons potència
        es_trifasic = potencia and potencia in POTENCIES_TRIFASIQUES or False
        es_trifasic = es_trifasic or pm_vals['tensio_pm'] == 400

        # Escullim el producte de lloguer
        if es_30:
            alq = 'ALQ30'
        elif es_tg:
            # Telegestió
            alq = es_trifasic and 'ALQ20' or 'ALQ19'
        elif es_dh:
            # DH
            alq = es_trifasic and 'ALQ07' or 'ALQ06'
        else:
            #Resta
            alq = es_trifasic and 'ALQ03' or 'ALQ02'

        # Calculem el preu per dia
        ctx = {'date': datetime.today().strftime('%Y-%m-%d')}
        preu_mes = pricelist_obj.price_get(cursor, uid, [tar_elec_id],
                                           preus[alq]['id'], 1.0,
                                           context=ctx)[tar_elec_id]

        preu = uom_obj._compute_price(cursor, uid, uoms['ALQ/mes'], preu_mes,
                                      uoms['ALQ/dia'])

        txt = (' '.join([pm_vals['mode_lectura'], str(tarifaatr), str(potencia),
                         str(pm_vals['tensio_pm'])])) + '->' + alq

        vals = {'preu_lloguer': round(preu, 6),
                'lloguer': True,
                'uom_id': uoms['ALQ/dia'],
                'txt': txt}

        return vals


GiscedataSwitchingAparell()


class GiscedataSwitching(osv.osv):
    """Classe per gestionar el canvi de comercialitzador
    """

    _name = 'giscedata.switching'
    _inherit = 'giscedata.switching'

    def _get_last_history_line(self, cr, uid, ids, name, arg, context=None):
        """ Nom de la situació de la instal·lació """
        res = dict([(i, '') for i in ids])

        for sw_obs in self.read(cr, uid, ids, ['user_observations'], context=context):
            if sw_obs['user_observations']:
                usr_obs = sw_obs['user_observations'].split('\n')

                if len(usr_obs) > 1:
                    usr_obs = [o for o in usr_obs if o]
                last_line = usr_obs[0] if usr_obs else ''

                res[sw_obs['id']] = last_line[:100]

        return res

    def _ff_get_data_accio(self, cursor, uid, ids, field_name, args, context=None):
        """Find the value of field data_accio in step '01'.
        Only search for process which are in ['a3', 'b1', 'm1', 'c1', 'c2']
        :param cursor: Database cursor
        :param uid: User id
        :param ids: cas atr id list
        :param context: Application context
        :returns data_accio
        """
        result = dict.fromkeys(ids, None)
        for sw_obs in self.read(cursor, uid, ids, ['proces_id'], context=context):
            if sw_obs['proces_id'][1].lower() in ['a3', 'b1', 'm1', 'c1', 'c2']:
                pas_obj = self.pool.get('giscedata.switching.{}.01'.format(sw_obs['proces_id'][1].lower()))
                pas_id = pas_obj.search(cursor, uid, [('sw_id','=',sw_obs['id'])])
                if pas_id:
                    result[sw_obs['id']] = pas_obj.read(cursor, uid, pas_id[0], ['data_accio'])['data_accio']

        return result

    def _get_pas_id(self, cr, uid, ids, context=None):
        res = []
        for sw_obs in self.read(cr, uid, ids, ['sw_id']):
            res.append(sw_obs['sw_id'][0])

        return res

    _columns = {
        'user_observations': fields.text('Observaciones del usuario'),
        'last_observation_line': fields.function(
            _get_last_history_line, method=True, type="char",
            size=100, string="Última línia de les observacions",
            store={
                'giscedata.switching': (
                    lambda self, cr, uid, ids, c=None: ids, ['user_observations'],
                    20
                ),
            }
        ),
        'data_accio': fields.function(
            _ff_get_data_accio, method=True, type="date",
            string="Data acció del pas 01",
            store={
                'giscedata.switching.a3.01': (_get_pas_id, ['data_accio'],20),
                'giscedata.switching.b1.01': (_get_pas_id, ['data_accio'],20),
                'giscedata.switching.c1.01': (_get_pas_id, ['data_accio'],20),
                'giscedata.switching.c2.01': (_get_pas_id, ['data_accio'],20),
                'giscedata.switching.m1.01': (_get_pas_id, ['data_accio'],20),
            }
        )
    }

    _defaults = {
        'user_observations': lambda *a: ''
    }

GiscedataSwitching()


class GiscedataFacturacioImportacioLinia(osv.osv):
    """Agrupació d'importacions"""

    _name = 'giscedata.facturacio.importacio.linia'
    _inherit = 'giscedata.facturacio.importacio.linia'

    def _get_last_history_line(self, cr, uid, ids, name, arg, context=None):
        """ Nom de la situació de la instal·lació """
        res = dict([(i, '') for i in ids])

        for f1 in self.read(cr, uid, ids, ['user_observations'],
                                context=context):
            if f1['user_observations']:
                usr_obs = f1['user_observations'].split('\n')

                if len(usr_obs) > 1:
                    usr_obs = [o for o in usr_obs if o]
                last_line = usr_obs[0] if usr_obs else ''

                res[f1['id']] = last_line[:100]

        return res

    _columns = {
        'user_observations': fields.text('Observacions de l\'usuari'),
        'last_observation_line': fields.function(
            _get_last_history_line, method=True, type="char",
            size=100, string="Última línia de les observacions",
            store={
                'giscedata.facturacio.importacio.linia': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['user_observations'],
                    20
                ),
            },
        )

    }
GiscedataFacturacioImportacioLinia()
