# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ooquery.expression import Field
from addons import get_module_resource
from osv import osv, fields
from addons.giscedata_facturacio.giscedata_polissa import _get_polissa_from_energy_invoice
from gestionatr.defs import TABLA_113, TABLA_129, TABLA_130, TABLA_131
from .exceptions import exceptions
from addons.giscedata_lectures_estimacio import giscedata_lectures_estimacio_helpers as estima_helper


TIPO_AUTOCONSUMO = TABLA_113
TIPO_AUTOCONSUMO_SEL = [(ac[0], u'[{}] - {}'.format(ac[0], ac[1])) for ac in TIPO_AUTOCONSUMO]

POLISSA_DATE_FIELDS = [
    'data_ultima_lectura', 'data_ultima_lectura_f1', 'data_alta',
    'data_alta_autoconsum', 'data_baixa', 'data_firma_contracte'
]

TARIFF_MAPPING = {
    "2.0A": "2.0TD",
    "2.0DHA": "2.0TD",
    "2.0DHS": "2.0TD",
    "2.1A": "2.0TD",
    "2.1DHA": "2.0TD",
    "2.1DHSA": "2.0TD",
    "2.1DHS": "2.0TD",
    "3.0A": "3.0TD",
    "6.1": "6.1TD",
    "3.1A": "6.1TD",
    "6.2": "6.2TD",
    "6.3": "6.3TD",
    "6.4": "6.4TD",
    "3.1A LB": "6.1TD",
    "6.1A": "6.1TD",
    "6.1B": "6.2TD"
}


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def update_contract_type(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}

        vals = vals.copy()

        # En funció del CNAE aplicar modificacions al tipus de contracte
        cfg_obj = self.pool.get('res.config')
        cnae_obj = self.pool.get('giscemisc.cnae')

        if "cnae" in vals and vals['cnae']:
             cnaes_ssaa = eval(cfg_obj.get(cursor, uid, 'sw_cnae_ssaa', '["3515", "3516", "3518", "3519"]'))
             cnae_name = cnae_obj.read(cursor, uid, vals['cnae'], ["name"])["name"]

             if cnae_name in cnaes_ssaa:
                 vals['contract_type'] = '05'

        return vals

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}

        vals = self.update_contract_type(cursor, uid, vals, context=context)
        res = super(GiscedataPolissa, self).create(cursor, uid, vals, context=context)

        if 'cnae' in vals or 'titular' in vals:
            self.set_category_eie(cursor, uid, res, context)

        return res

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}

        conf_obj = self.pool.get('res.config')
        change_contract_type = int(conf_obj.get(cursor, uid, "onchange_contract_type_by_cnae", 0))
        if change_contract_type:
            vals = self.update_contract_type(cursor, uid, vals, context=context)
        res = super(GiscedataPolissa, self).write(cursor, uid, ids, vals, context=context)

        if 'cnae' in vals or 'titular' in vals:
            self.set_category_eie(cursor, uid, ids, context)

        return res

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        """Funció per fer cerques en dates buides'.
        """
        for idx, arg in enumerate(args):
            if len(arg) == 3:
                field, operator, match = arg
                if field in POLISSA_DATE_FIELDS and operator == '>=' and match >= '9999-01-01':
                    args[idx][1] = '='
                    args[idx][2] = False
        return super(GiscedataPolissa, self).search(cr, user, args, offset, limit, order, context, count)

    def check_modifiable_polissa(
        self, cursor, uid, polissa_id, skip_atr_check=False, excluded_cases=None, context=None
    ):
        """
        Things to check before allowing modcons to the contract.
        - Contract doesn't have ANY pending modcons
        - Contract doesn't have ANY pending ATR cases
        """
        if context is None:
            context = {}

        if excluded_cases is None:
            excluded_cases = []

        sw_obj = self.pool.get('giscedata.switching')

        polissa = self.browse(cursor, uid, polissa_id, context=context)

        if polissa.state != 'activa':
            raise exceptions.PolissaNotActive(polissa.name)

        prev_modcon = polissa.modcontractuals_ids[0]
        if prev_modcon.state == 'pendent':
            raise exceptions.PolissaModconPending(polissa.name)

        excluded_cases.append('R1')
        atr_case = sw_obj.search(cursor, uid, [
            ('cups_polissa_id', '=', polissa.id),
            ('state', 'in', ['open', 'draft', 'pending']),
            ('proces_id.name', 'not in', excluded_cases),
        ])

        if atr_case and not skip_atr_check:
            raise exceptions.PolissaSimultaneousATR(polissa.name)

        return True

    def get_new_potencies(self, potencies_periode, new_tariff_code):
        potencies_periode = list(potencies_periode)
        if len(potencies_periode) == 6:
            return potencies_periode
        if new_tariff_code == '2.0TD':
            return [potencies_periode[0], potencies_periode[0]]

        p2_to_p5 = potencies_periode[0] if potencies_periode[0] > potencies_periode[1] else potencies_periode[1]
        p6 = p2_to_p5 if p2_to_p5 > potencies_periode[2] else potencies_periode[2]
        if new_tariff_code == '3.0TD':
            return [
                potencies_periode[0],
                p2_to_p5,
                p2_to_p5,
                p2_to_p5,
                p2_to_p5,
                p6,
            ]

        if new_tariff_code == '6.1TD':
            return [
                potencies_periode[0],
                p2_to_p5,
                p2_to_p5,
                p2_to_p5,
                p2_to_p5,
                p6,
            ]
        return potencies_periode

    def get_new_tariff(self, cursor, uid, ids):
        if not isinstance(ids, list):
            ids = [ids]
        res = dict.fromkeys([str(_id) for _id in ids], {'tarifa_codi':'', 'potencies':[]})
        for pol in self.browse(cursor, uid, ids):
            pol_reads = self.read(cursor, uid, pol['id'], ['tarifa_codi', 'tensio'])
            if pol_reads['tarifa_codi'].startswith("3.1") and pol_reads['tensio'] > 30000:
                new_tariff_code = "6.2TD"
            else:
                new_tariff_code = TARIFF_MAPPING[pol_reads['tarifa_codi']]

            res[str(pol['id'])]['tarifa_codi'] = new_tariff_code

            potencies_periode = []
            for potencia_periode in pol['potencies_periode']:
                potencies_periode.append(potencia_periode.potencia)

            res[str(pol['id'])]['potencies'] = self.get_new_potencies(potencies_periode, new_tariff_code) if potencies_periode != [] else []

        return res

    def _fnct_info_gestio_endarrerida_curta(self, cursor, uid, ids, field_name, arg, context=None):
        """
        Obté la versió curta de la informació de la gestió endarrerida. La
        versió curta no és més que els primers 50 caràcters del camp de la
        informació de la gestió endarrerida.
        @param cursor: DB Cursor.
        @type cursor: sql_db.Cursor
        @param uid: Identificador de l'usuari que consulta el camp.
        @type uid: int
        @param ids: Identificadors de les pòlisses a les quals se'ls està
        consultant la versió curta de la informació de la gestió endarrerida.
        @type ids: list[int]
        @param field_name: Nom del camp que invoca aquesta funció.
        @type field_name: str
        @param arg: ?
        @param context: OpenERP context
        @type context: dict
        @return:
        """
        if context is None:
            context = {}
        polissa_f = ['info_gestio_endarrerida']
        polissa_vs = self.read(cursor, uid, ids, polissa_f, context=context)
        res = {}

        for polissa_v in polissa_vs:
            polissa_id = polissa_v['id']
            info_gestio_endarrerida = polissa_v['info_gestio_endarrerida']
            longitud_camp_curt = self._columns[field_name].size
            info_gestio_endarrerida_curta = ''

            if info_gestio_endarrerida:
                info_gestio_endarrerida_curta = info_gestio_endarrerida[:longitud_camp_curt]

            res[polissa_id] = info_gestio_endarrerida_curta

        return res

    def _fnct_search_info_gestio_endarrerida_curta(self, cursor, uid, obj, name, args, context=None):
        if context is None:
            context = {}

        if args:
            return [
                ('info_gestio_endarrerida', args[0][1], args[0][2])
            ]
        else:
            return []

    def _get_fact_enderrerida_ids(self, cursor, uid, context=None):
        """
        Funció de cerca de les ids de le polisses amb facturacio endarrerida
        """
        if context is None:
            context = {}

        cfg_obj = self.pool.get('res.config')
        nom_conf = 'periode_polissa_facturacio_endarrerida'
        periode = float(cfg_obj.get(cursor, uid, nom_conf, 1.33))

        ids = []
        for facturacio in [1, 2]:
            dies = facturacio * 30 * periode
            data_anterior = datetime.now() - timedelta(dies)

            baixa_sql_file = get_module_resource(
                'som_polissa', 'sql', 'baixa_ids.sql'
            )
            baixa_sql = open(baixa_sql_file, 'r').read()
            cursor.execute(baixa_sql)
            baixa_res = cursor.fetchall()
            baixa_ids = [x[0] for x in baixa_res]

            # Adds unsubscribed contracts
            ids.extend(baixa_ids)

            grans_sql_file = get_module_resource(
                'som_polissa', 'sql', 'grans_contractes_ids.sql'
            )
            grans_sql = open(grans_sql_file, 'r').read()
            cursor.execute(grans_sql)
            grans_res = cursor.fetchall()
            grans_ids = [x[0] for x in grans_res]

            # Adds contracts with Category Grans Consums
            ids.extend(grans_ids)

            reg_ids = self.search(cursor, uid,
                                  [('facturacio', '=', facturacio),
                                   '|',
                                   '&', ('data_ultima_lectura', '<',
                                         data_anterior),
                                   ('data_ultima_lectura', '!=', False),
                                   '&', ('data_alta', '<', data_anterior),
                                   ('data_ultima_lectura', '=', False)])
            ids.extend(reg_ids)
        return ids

    def _search_fact_endarrerida(self, cursor, uid, obj, name, args,
                                 context=None):
        """
        Funció de cerca de facturacio endarrerida
        """
        return [('id', 'in', self._get_fact_enderrerida_ids(cursor, uid, context=context))]

    def _ff_fact_endarrerida(self, cursor, uid, ids, field_name, args, context=None):

        """ Marquem una factura com a endarrerida:
                * Fa més de 1.33 * facturacio dies que no es factura
                * La pólissa no té cap factura fa 1.33 * facturacio
                  dies que està facturada
        """
        res = super(GiscedataPolissa, self)._ff_fact_endarrerida(cursor, uid, ids, field_name, args, context=context)
        pol_ids = self._get_fact_enderrerida_ids(cursor, uid, context=context)
        res.update(dict.fromkeys(pol_ids, True))
        return res

    def set_category_eie(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if not isinstance(ids, list):
            ids = [ids]

        cnae_eie = False
        nif_eie = False

        partner_obj = self.pool.get('res.partner')
        polissa_obj = self.pool.get('giscedata.polissa')
        imd_obj = self.pool.get('ir.model.data')

        domestic_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_domestic'
        )[1]
        eie_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_entitat_o_empresa'
        )[1]
        eie_cnae_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_eie_CNAE_no_domestic'
        )[1]
        eie_vat_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_eie_persona_juridic'
        )[1]
        eie_cnae_vat_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa', 'categ_eie_CNAE_CIF'
        )[1]

        for _id in ids:
            cnae_eie = False
            nif_eie = False
            categories_ids = []
            pol = self.browse(cursor, uid, _id)

            if pol.cnae.name not in ['9810','9820']:
                cnae_eie = True
            if partner_obj.is_enterprise_vat(pol.titular.vat):
                nif_eie = True

            if cnae_eie and nif_eie:
                categories_ids.append((4,eie_id))
                categories_ids.append((4,eie_cnae_vat_id))
                categories_ids.append((3,eie_cnae_id))
                categories_ids.append((3,domestic_id))
                categories_ids.append((3,eie_vat_id))
            elif cnae_eie and not nif_eie:
                categories_ids.append((4,eie_id))
                categories_ids.append((4,eie_cnae_id))
                categories_ids.append((3,domestic_id))
                categories_ids.append((3,eie_cnae_vat_id))
                categories_ids.append((3,eie_vat_id))
            elif not cnae_eie and nif_eie:
                categories_ids.append((4,eie_id))
                categories_ids.append((4,eie_vat_id))
                categories_ids.append((3,domestic_id))
                categories_ids.append((3,eie_cnae_id))
                categories_ids.append((3,eie_cnae_vat_id))
            else:
                categories_ids.append((4,domestic_id))
                categories_ids.append((3,eie_id))
                categories_ids.append((3,eie_vat_id))
                categories_ids.append((3,eie_cnae_id))
                categories_ids.append((3,eie_cnae_vat_id))

            polissa_obj.write(cursor, uid, [_id], {'category_id': categories_ids})

    def _ff_get_dies_lectures_facturada_f1(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}

        res = dict.fromkeys(ids, 0)
        if ids:
            pols_dates = self.read(cursor, uid, ids, ['data_ultima_lectura', 'data_ultima_lectura_f1', 'data_alta'])
            for p_dates in pols_dates:
                data_desde = p_dates['data_ultima_lectura'] or p_dates['data_alta']
                data_fins = p_dates['data_ultima_lectura_f1']
                if data_fins and data_desde:
                    res[p_dates['id']] = (datetime.strptime(data_fins, '%Y-%m-%d') - datetime.strptime(data_desde, '%Y-%m-%d')).days

        return res

    def wkf_activa(self, cursor, uid, ids):
        if not isinstance(ids, list):
            ids = [ids]

        payment_mode_o = self.pool.get('payment.mode')
        payment_mode_id = payment_mode_o.search(cursor, uid, [('name', '=', 'ENGINYERS')])
        self.write(cursor, uid, ids, {'payment_mode_id': payment_mode_id[0]})

        return super(GiscedataPolissa, self).wkf_activa(cursor, uid, ids)

    def copy_data(self, cursor, uid, id, default=None, context=None):
        if context is None:
            context = {}

        if default is None:
            default = {}

        payment_mode_o = self.pool.get('payment.mode')
        payment_mode_id = payment_mode_o.search(cursor, uid, [('name', '=', 'ENGINYERS')])
        default.update({'payment_mode_id': payment_mode_id[0]})
        return super(GiscedataPolissa, self).copy_data(cursor, uid, id, default, context=context)

    def _ff_search_ssaa(self, cursor, uid, ids, field_name, args, context=None):
        if context is None:
            context = {}
        acg_obj = self.pool.get('giscedata.autoconsum.generador')
        autoconsum_ids = []
        if args[0][2] == 1:
            val = 'S'
        else:
            val = 'N'
        generador_ids = acg_obj.search(cursor, uid, [('ssaa', '=', val)], context=context)
        ac_ids = acg_obj.read(cursor, uid, generador_ids, ['autoconsum_id'], context=context)
        for ac_id in ac_ids:
            autoconsum_ids.append(ac_id['autoconsum_id'][0])
        polissa_ids = self.search(cursor, uid, [('autoconsum_id', 'in', autoconsum_ids)])

        return [('id', 'in', polissa_ids)]

    def _get_ssaa(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        acg_obj = self.pool.get('giscedata.autoconsum.generador')
        ac_obj = self.pool.get('giscedata.autoconsum')
        res = dict.fromkeys(ids, False)

        for pol_id in ids:
            autoconsum_id = self.read(cursor, uid, pol_id, ['autoconsum_id'], context=context)
            if autoconsum_id.get('autoconsum_id'):
                autoconsum_id = autoconsum_id['autoconsum_id'][0]
                generador_id = acg_obj.search(cursor, uid, [('autoconsum_id', '=', autoconsum_id)], context=context)
                if generador_id:
                    ssaa = acg_obj.read(cursor, uid, generador_id[0], ['ssaa'], context=context)
                    if ssaa['ssaa'] == 'S':
                        res[pol_id] = True

        return res

    def _ff_search_cups_np(self, cursor, uid, ids, field_name, args, context=None):
        if context is None:
            context = {}
        cups_obj = self.pool.get('giscedata.cups.ps')

        cups_ids = cups_obj.search(cursor, uid, [('id_municipi.state.name', args[0][1], args[0][2])])
        polissa_ids = self.search(cursor, uid, [('cups', 'in', cups_ids)])

        return [('id', 'in', polissa_ids)]

    def _get_provincia_cups(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        cups_obj = self.pool.get('giscedata.cups.ps')
        res = dict.fromkeys(ids, False)

        for pol_id in ids:
            provincia = cups_obj.q(cursor, uid).read(['id_provincia']).where([('polissa_polissa', '=', pol_id)])
            if provincia:
                provincia = provincia[0]['id_provincia'][1]
                res[pol_id] = provincia

        return res

    def _ff_search_tipus_cups(self, cursor, uid, ids, field_name, args, context=None):
        if context is None:
            context = {}
        polissa_ids = []
        ac_cups_obj = self.pool.get('giscedata.autoconsum.cups.autoconsum')
        cups_ac_ids = ac_cups_obj.search(cursor, uid, [('tipus_cups', '=', args[0][2])])
        cups_ac_data = ac_cups_obj.read(cursor, uid, cups_ac_ids, ['autoconsum_id', 'cups_id'], context=context)
        for data in cups_ac_data:
            if data.get('autoconsum_id') and data.get('cups_id'):
                polissa_id = self.search(cursor, uid, [('cups', '=', data['cups_id'][0]), ('autoconsum_id', '=', data['autoconsum_id'][0])])
                if polissa_id:
                    polissa_ids.append(polissa_id[0])

        return [('id', 'in', polissa_ids)]

    def _get_tipus_cups(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        ac_cups_obj = self.pool.get('giscedata.autoconsum.cups.autoconsum')
        res = dict.fromkeys(ids, False)
        for pol_id in ids:
            polissa_data = self.read(cursor, uid, pol_id, ['autoconsum_id', 'cups'], context=context)
            if polissa_data.get('autoconsum_id') and polissa_data.get('cups'):
                ac_cups_id = ac_cups_obj.search(cursor, uid, [('autoconsum_id', '=', polissa_data['autoconsum_id'][0]), ('cups_id', '=', polissa_data['cups'][0])], context=context)
                if ac_cups_id:
                    tipus_cups = ac_cups_obj.read(cursor, uid, ac_cups_id[0], ['tipus_cups'], context=context)['tipus_cups']
                    res[pol_id] = tipus_cups

        return res

    def _ff_search_bateria_virtual(self, cursor, uid, ids, field_name, args, context=None):
        if context is None:
            context = {}
        polissa_ids = []
        bat_pol_o = self.pool.get('giscedata.bateria.virtual.polissa')
        bat_pol_ids = bat_pol_o.search(cursor, uid, [('bateria_id.name', '=', args[0][2])])
        bat_pol_data = bat_pol_o.read(cursor, uid, bat_pol_ids, ['polissa_id'], context=context)
        for data in bat_pol_data:
            if data.get('polissa_id'):
                polissa_ids.append(data['polissa_id'][0])

        return [('id', 'in', polissa_ids)]
    def _get_bateria_virtual(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        res = dict.fromkeys(ids, False)
        bat_pol_o = self.pool.get('giscedata.bateria.virtual.polissa')
        for pol_id in ids:
            bat_pol_id = bat_pol_o.search(cursor, uid, [('polissa_id', '=', pol_id)])
            if bat_pol_id and isinstance(bat_pol_id, list):
                bat_pol_id = bat_pol_id[0]
            bv = bat_pol_o.read(cursor, uid, bat_pol_id, ['bateria_id'], context=context)
            if bv and bv.get('bateria_id'):
                res[pol_id] = bv['bateria_id'][1]

    def _ff_search_tipus_installacio(self, cursor, uid, ids, field_name, args, context=None):
        if context is None:
            context = {}
        acg_obj = self.pool.get('giscedata.autoconsum.generador')
        autoconsum_ids = []

        generador_ids = acg_obj.search(cursor, uid, [('tipus_installacio', '=', args[0][2])], context=context)
        ac_ids = acg_obj.read(cursor, uid, generador_ids, ['autoconsum_id'], context=context)
        for ac_id in ac_ids:
            if ac_id.get('autoconsum_id'):
                autoconsum_ids.append(ac_id['autoconsum_id'][0])
        polissa_ids = self.search(cursor, uid, [('autoconsum_id', 'in', autoconsum_ids)])

        return [('id', 'in', polissa_ids)]

    def _get_tipus_installacio(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        acg_obj = self.pool.get('giscedata.autoconsum.generador')
        ac_obj = self.pool.get('giscedata.autoconsum')
        res = dict.fromkeys(ids, False)

        for pol_id in ids:
            autoconsum_id = self.read(cursor, uid, pol_id, ['autoconsum_id'], context=context)
            if autoconsum_id.get('autoconsum_id'):
                autoconsum_id = autoconsum_id['autoconsum_id'][0]
                generador_id = acg_obj.search(cursor, uid, [('autoconsum_id', '=', autoconsum_id)], context=context)
                if generador_id:
                    tipus_installacio = acg_obj.read(cursor, uid, generador_id[0], ['tipus_installacio'], context=context)
                    if tipus_installacio.get('tipus_installacio'):
                        res[pol_id] = tipus_installacio['tipus_installacio']

        return res

    def _ff_search_bateria_activa(self, cursor, uid, obj, field_name, args, context=None):
        if context is None:
            context = {}
        bat_virtual_polissa_obj = self.pool.get("giscedata.bateria.virtual.polissa")
        te_bateria = args[0][2]
        data_avui = datetime.today().strftime("%Y-%m-%d")
        search_vals = [
            ('data_inici', '<=', data_avui),
            '|', ('data_final', '>', data_avui),
                 ('data_final', '=', False)
        ]

        bat_polissa_ids = bat_virtual_polissa_obj.search(cursor, uid, search_vals, context=context)
        bat_polisses = bat_virtual_polissa_obj.read(cursor, uid, bat_polissa_ids, ['polissa_id'], context=context)
        polissa_ids = [bat_polissa['polissa_id'][0] for bat_polissa in bat_polisses]
        if te_bateria:
            return [('id', 'in', polissa_ids)]
        else:
            return [('id', 'not in', polissa_ids)]

    def _ff_search_data_inici_bat(self, cursor, uid, obj, field_name, args, context=None):
        if context is None:
            context = {}
        bat_virtual_polissa_obj = self.pool.get("giscedata.bateria.virtual.polissa")
        operador = args[0][1]
        data = args[0][2]
        search_vals = [
            ('data_inici', operador, data),
        ]
        bat_polissa_ids = bat_virtual_polissa_obj.search(cursor, uid, search_vals, context=context)
        bat_polisses = bat_virtual_polissa_obj.read(cursor, uid, bat_polissa_ids, ['polissa_id'], context=context)
        polissa_ids = [bat_polissa['polissa_id'][0] for bat_polissa in bat_polisses]
        return [('id', 'in', polissa_ids)]

    def _ff_search_data_final_bat(self, cursor, uid, obj, field_name, args, context=None):
        if context is None:
            context = {}
        bat_virtual_polissa_obj = self.pool.get("giscedata.bateria.virtual.polissa")
        operador = args[0][1]
        data = args[0][2]
        search_vals = [
            ('data_final', operador, data),
        ]
        bat_polissa_ids = bat_virtual_polissa_obj.search(cursor, uid, search_vals, context=context)
        bat_polisses = bat_virtual_polissa_obj.read(cursor, uid, bat_polissa_ids, ['polissa_id'], context=context)
        polissa_ids = [bat_polissa['polissa_id'][0] for bat_polissa in bat_polisses]
        return [('id', 'in', polissa_ids)]

    def _ff_get_info_bateria(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        bat_virtual_polissa_obj = self.pool.get("giscedata.bateria.virtual.polissa")
        q = bat_virtual_polissa_obj.q(cursor, uid)
        default_dict = {
            'bateria_activa': False,
            'data_activacio_bateria': False,
            'data_baixa_bateria': False
        }
        res = dict.fromkeys(ids, default_dict)
        data_avui = datetime.today().strftime("%Y-%m-%d")

        sql = q.select([
            'id', 'data_inici', 'data_final', 'polissa_id'
        ], only_active=False).where([
            ('polissa_id', 'in', ids)
        ])
        cursor.execute(*sql)
        for row in cursor.dictfetchall():
            bateria_activa = False
            if row['data_inici'] <= data_avui and row['data_final'] > data_avui or not row['data_final']:
                bateria_activa = True
            res[row['polissa_id']] = {
                'bateria_activa': bateria_activa,
                'data_activacio_bateria': row['data_inici'],
                'data_baixa_bateria': row['data_final'] if row['data_final'] else False
            }
        return res

    def consum_diari(self, cursor, uid, polissa_id, dies, data_ref=None, separat=None,
                     context=None):
        """Calculem el consum diari a 14 mesos"""
        if isinstance(polissa_id, (list, tuple)):
            polissa_id = polissa_id[0]

        consum_diari = estima_helper.consum_diari_separat(cursor, uid, polissa_id,
                                                  dies=365, data_ref=data_ref, separat=True)

        return consum_diari

    _columns = {
        'info_gestio_endarrerida': fields.text('Informació gestió endarrerida'),
        'info_gestio_endarrerida_curta': fields.function(
            fnct=_fnct_info_gestio_endarrerida_curta, type='char', size=64,
            string='Informació gestions', method=True, fnct_search=_fnct_search_info_gestio_endarrerida_curta,
        ),
        'facturacio_endarrerida': fields.function(_ff_fact_endarrerida,
                                                  method=True, type='boolean',
                                                  string='Facturació '
                                                         'endarrerida',
                                                  fnct_search=_search_fact_endarrerida,
                                                  readonly=True),
        'info_gestions_massives': fields.text('Informació gestions massives'),
        'dies_lectures_facturada_f1': fields.function(
            _ff_get_dies_lectures_facturada_f1, method=True, type='float', digits=(8, 1),
            string='Dif. dies lectures F1 i facturades', readonly=True,
            help="Data última lectura F1 - data última lectura facturada (si no té data facturada real, agafa la data d'alta de la pòlissa).",
            store={
                'giscedata.polissa': (
                    lambda self, cr, uid, ids, c={}: ids,
                    ['name', 'data_ultima_lectura', 'data_ultima_lectura_f1', 'data_alta'], 20
                ),
                'account.invoice': (
                    _get_polissa_from_energy_invoice, ['state'], 20
                )
            }
        ),
        'bateria_activa': fields.function(
            _ff_get_info_bateria, type='boolean', fnct_search=_ff_search_bateria_activa, method=True, multi=True,
            string='Bateria activa',
        ),
        'data_activacio_bateria': fields.function(
            _ff_get_info_bateria, type='date', fnct_search=_ff_search_data_inici_bat, method=True, multi=True,
            string='Data activació bateria',
        ),
        'data_baixa_bateria': fields.function(
            _ff_get_info_bateria, type='date', fnct_search=_ff_search_data_final_bat, method=True, multi=True,
            string='Data baixa bateria',
        ),
        'esquema_mesura': fields.selection(TABLA_130, 'Esquema mesura'),
        'ssaa': fields.function(_get_ssaa, fnct_search=_ff_search_ssaa, method=True, string=u"SSAA", type="boolean"),
        'cups_np': fields.function(_get_provincia_cups, fnct_search=_ff_search_cups_np, method=True, type="char", string='Provincia (CUPS)',
            size=24),
        'tipus_cups': fields.function(_get_tipus_cups, fnct_search=_ff_search_tipus_cups, method=True, selection=TABLA_131, string='Tipus CUPS',
            readonly=True, type="selection"),
        'bateria_virtual': fields.function(_get_bateria_virtual, fnct_search=_ff_search_bateria_virtual, method=True, type="char", string='Codi BV',
            size=24),
        'tipus_installacio': fields.function(_get_tipus_installacio, fnct_search=_ff_search_tipus_installacio, method=True, type="selection",selection=TABLA_129, string='Tipus instal.lació',
                                           ),
    }


GiscedataPolissa()
