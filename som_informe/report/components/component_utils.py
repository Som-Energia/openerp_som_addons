
# -*- encoding: utf-8 -*-
from gestionatr.utils import get_description as gestion_atr_get_description
from datetime import datetime

magnitud_a_tipus = {
    'AE': 'energia',
    'AS': 'generacio',
    'PM': 'potencia',
    'EP': 'exces_potencia',
    'R1': 'reactiva',
    'R2': 'reactiva',
    'R3': 'reactiva',
    'R4': 'reactiva',
}

magnitud_a_unit = {
    'AE': 'kWh',
    'AS': 'kWh',
    'PM': 'kW',
    'EP': 'kW',
    'R1': 'kVarh',
    'R2': 'kVarh',
    'R3': 'kVarh',
    'R4': 'kVarh',
}

periode_a_name = {
    '91': 'P1',
    '92': 'P2',
    '93': 'P3',
    '9392': 'P2',
    'A1': 'P1',
    'A2': 'P2',
    'A3': 'P3',
    'A4': 'P4',
    'A5': 'P5',
    'A6': 'P6',
}

def get_unit_magnitude(magnitud):
    return magnitud_a_unit.get(magnitud, 'eV')

def get_invoice_line(invoice, magnitud, periode):
    if magnitud == 'PM' and periode == '93':
        periode = '9392'

    tipus = magnitud_a_tipus.get(magnitud, None)
    name = periode_a_name.get(periode, None)
    if not name or not tipus:
        return None

    for l in invoice.linia_ids:
        if l.name == name and l.tipus == tipus:
            return l
    return None

def to_date(str_date, hours = False):
    if not str_date:
        return None
    if not hours:
        return datetime.strptime(str_date[0:10],'%Y-%m-%d')
    return datetime.strptime(str_date,'%Y-%m-%d %H:%M:%S')

def to_string(obj_date, hours = False):
    if not obj_date:
        return ""
    if not hours:
        return obj_date.strftime('%d-%m-%Y')
    return obj_date.strftime('%d-%m-%Y %H:%M:%S')

def dateformat(str_date, hours = False):
    if not str_date:
        return ""
    if not hours:
        return datetime.strptime(str_date[0:10],'%Y-%m-%d').strftime('%d-%m-%Y')
    return datetime.strptime(str_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')

def get_description(key, table_name, on_error_return_false = False):
    try:
        return gestion_atr_get_description(key, table_name)
    except (ValueError, KeyError):
        if on_error_return_false:
            return False
        return "ERROR {} no trobat a {}.".format(key, table_name)

def is_domestic(pol):
    for cat in pol.category_id:
        if cat.code == 'DOM':
            return True
    return False

def is_enterprise(pol):
    return not is_domestic(pol)

def has_category(pol, category_ids):
    for cat in pol.category_id:
        if cat.id in category_ids:
            return True
    return False

def get_origen_lectura(self, lectura):
    """Busquem l'origen de la lectura cercant-la a les lectures de facturació"""
    res = {lectura.data_actual: '',
        lectura.data_anterior: ''}

    lectura_obj = lectura.pool.get('giscedata.lectures.lectura')
    tarifa_obj = lectura.pool.get('giscedata.polissa.tarifa')
    origen_obj = lectura.pool.get('giscedata.lectures.origen')
    origen_comer_obj = lectura.pool.get('giscedata.lectures.origen_comer')

    estimada_id = origen_obj.search(self.cursor, self.uid, [('codi', '=', '40')])[0]
    sin_lectura_id = origen_obj.search(self.cursor, self.uid, [('codi', '=', '99')])[0]
    estimada_som_id = origen_comer_obj.search(self.cursor, self.uid, [('codi', '=', 'ES')])[0]
    calculada_som_id = origen_obj.search(self.cursor, self.uid, [('codi', '=', 'LC')])
    calculada_som_id = calculada_som_id[0] if calculada_som_id else None

    #Busquem la tarifa
    tarifa_id = tarifa_obj.search(self.cursor, self.uid, [('name', '=', lectura.name[:-5])])
    if tarifa_id:
        tipus = lectura.tipus == 'activa' and 'A' or 'R'

        search_vals = [('comptador', '=', lectura.comptador),
                    ('periode.name', '=', lectura.name[-3:-1]),
                    ('periode.tarifa', '=', tarifa_id[0]),
                    ('tipus', '=', tipus),
                    ('name', 'in', [lectura.data_actual,
                                    lectura.data_anterior])]
        lect_ids = lectura_obj.search(self.cursor, self.uid, search_vals)
        lect_vals = lectura_obj.read(self.cursor, self.uid, lect_ids,
                                    ['name', 'origen_comer_id', 'origen_id'])
        for lect in lect_vals:
            # En funció dels origens, escrivim el text
            # Si Estimada (40) o Sin Lectura (99) i Estimada (ES): Estimada Somenergia
            # Si Estimada (40) o Sin Lectura (99) i F1/Q1/etc...(!ES): Estimada distribuïdora
            # La resta: Real
            origen_txt = _(u"real")
            if lect['origen_id'][0] in [ estimada_id, sin_lectura_id ]:
                if lect['origen_comer_id'][0] == estimada_som_id:
                    origen_txt = _(u"calculada per Som Energia")
                else:
                    origen_txt = _(u"estimada distribuïdora")
            if lect['origen_id'][0] == calculada_som_id:
                origen_txt = _(u"calculada segons CCH")
            res[lect['name']] = "%s" % (origen_txt)

    return res
