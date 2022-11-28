# -*- coding: utf-8 -*-
from tools.translate import _
from .. import base_component_data
from ..base_component_utils import val, dateformat, getYMDdate

class ComponentReadingsDataData(base_component_data.BaseComponentData):

    def init_origens(self):
        origen_obj = self.report.pool.get('giscedata.lectures.origen')
        origen_comer_obj = self.report.pool.get('giscedata.lectures.origen_comer')

        self.estimada_id = origen_obj.search(self.cursor, self.uid, [('codi', '=', '40')])[0]
        self.sin_lectura_id = origen_obj.search(self.cursor, self.uid, [('codi', '=', '99')])[0]
        self.estimada_som_id = origen_comer_obj.search(self.cursor, self.uid, [('codi', '=', 'ES')])[0]
        self.calculada_som_id = origen_obj.search(self.cursor, self.uid, [('codi', '=', 'LC')])
        self.calculada_som_id = self.calculada_som_id[0] if self.calculada_som_id else None

    def get_origen_lectura(self, lectura):
        """Busquem l'origen de la lectura cercant-la a les lectures de facturació"""
        res = {lectura.data_actual: '',
            lectura.data_anterior: ''}

        lectura_obj = self.report.pool.get('giscedata.lectures.lectura')
        tarifa_obj = self.report.pool.get('giscedata.polissa.tarifa')

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
                if lect['origen_id'][0] in [ self.estimada_id, self.sin_lectura_id ]:
                    if lect['origen_comer_id'][0] == self.estimada_som_id:
                        origen_txt = _(u"calculada per Som Energia")
                    else:
                        origen_txt = _(u"estimada distribuïdora")
                if lect['origen_id'][0] == self.calculada_som_id:
                    origen_txt = _(u"calculada")
                res[lect['name']] = "%s" % (origen_txt)

        return res

    def get_data(self):

        data = base_component_data.BaseComponentData.get_data(self)

        self.init_origens()
        fact = self.fact
        """
        Calculate the active and reactive energy readings data
        """

        periodes_a = sorted(list(set([lectura.name[-3:-1]
                                    for lectura in fact.lectures_energia_ids
                                    if lectura.tipus == 'activa' and lectura.magnitud == 'AE'])))
        periodes_r = sorted(list(set([lectura.name[-3:-1]
                                    for lectura in fact.lectures_energia_ids
                                    if lectura.tipus == 'reactiva' and lectura.magnitud == 'R1'])))
        periodes_c = sorted(list(set([lectura.name[-3:-1]
                                    for lectura in fact.lectures_energia_ids
                                    if lectura.tipus == 'reactiva' and lectura.magnitud == 'R4'])))
        periodes_g = sorted(list(set([lectura.name[-3:-1]
                                    for lectura in fact.lectures_energia_ids
                                    if lectura.tipus == 'activa' and lectura.magnitud == 'AS'])))

        lectures_a = {}
        lectures_r = {}
        lectures_c = {}
        lectures_g = {}

        lectures_real_a = {}
        lectures_real_r = {}
        lectures_real_c = {}
        lectures_real_g = {}

        for lectura in fact.lectures_energia_ids:
            origens = self.get_origen_lectura(lectura)
            if lectura.tipus == 'activa' and lectura.magnitud == 'AE':
                lectures_a.setdefault(lectura.comptador,[])
                lectures_a[lectura.comptador].append((lectura.name[-3:-1],
                                                    val(lectura.lect_anterior),
                                                    val(lectura.lect_actual),
                                                    val(lectura.consum),
                                                    dateformat(lectura.data_anterior),
                                                    dateformat(lectura.data_actual),
                                                    origens[lectura.data_anterior],
                                                    origens[lectura.data_actual],
                                                    val(lectura.ajust),
                                                    val(lectura.motiu_ajust),
                                                    ))
                lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.pool_lectures if lectura_real.tipus == "A" and "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,9,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                lectures_real_a.setdefault(lectura.comptador,[])
                if len(lectura_real)>0:
                    lectures_real_a[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura),dateformat(lectura_real[0].name)))
                else:
                    lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.lectures if lectura_real.tipus == "A" and  "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,9,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                    if len(lectura_real)>0:
                        lectures_real_a[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura), dateformat(lectura_real[0].name)))

            elif lectura.tipus == 'activa' and lectura.magnitud == 'AS':
                lectures_g.setdefault(lectura.comptador,[])
                lectures_g[lectura.comptador].append((lectura.name[-3:-1],
                                                    val(lectura.lect_anterior),
                                                    val(lectura.lect_actual),
                                                    val(lectura.consum),
                                                    dateformat(lectura.data_anterior),
                                                    dateformat(lectura.data_actual),
                                                    origens[lectura.data_anterior],
                                                    origens[lectura.data_actual],
                                                    val(lectura.ajust),
                                                    val(lectura.motiu_ajust),
                                                    ))
                lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.pool_lectures if lectura_real.tipus == "A" and "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,9,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                lectures_real_g.setdefault(lectura.comptador,[])
                if len(lectura_real)>0:
                    lectures_real_g[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura),dateformat(lectura_real[0].name)))
                else:
                    lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.lectures if lectura_real.tipus == "A" and  "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,9,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                    if len(lectura_real)>0:
                        lectures_real_g[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura), dateformat(lectura_real[0].name)))

            elif lectura.tipus == 'reactiva' and lectura.magnitud == 'R1':
                lectures_r.setdefault(lectura.comptador,[])
                lectures_r[lectura.comptador].append((lectura.name[-3:-1],
                                                    val(lectura.lect_anterior),
                                                    val(lectura.lect_actual),
                                                    val(lectura.consum),
                                                    dateformat(lectura.data_anterior),
                                                    dateformat(lectura.data_actual),
                                                    origens[lectura.data_anterior],
                                                    origens[lectura.data_actual],
                                                    ))
                lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.pool_lectures if lectura_real.tipus == "R" and "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                lectures_real_r.setdefault(lectura.comptador,[])
                if len(lectura_real)>0:
                    lectures_real_r[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura),dateformat(lectura_real[0].name)))
                else:
                    lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.lectures if lectura_real.tipus == "R" and  "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                    if len(lectura_real)>0:
                        lectures_real_r[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura),dateformat(lectura_real[0].name)))

            elif lectura.tipus == 'reactiva' and lectura.magnitud == 'R4':
                lectures_c.setdefault(lectura.comptador,[])
                lectures_c[lectura.comptador].append((lectura.name[-3:-1],
                                                    val(lectura.lect_anterior),
                                                    val(lectura.lect_actual),
                                                    val(lectura.consum),
                                                    dateformat(lectura.data_anterior),
                                                    dateformat(lectura.data_actual),
                                                    origens[lectura.data_anterior],
                                                    origens[lectura.data_actual],
                                                    ))
                lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.pool_lectures if lectura_real.tipus == "R" and "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                lectures_real_c.setdefault(lectura.comptador,[])
                if len(lectura_real)>0:
                    lectures_real_c[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura),dateformat(lectura_real[0].name)))
                else:
                    lectura_real = sorted([lectura_real for lectura_real in lectura.comptador_id.lectures if lectura_real.tipus == "R" and  "{} ({})".format(lectura_real.periode.tarifa.name,lectura_real.periode.product_id.name) == lectura.name and lectura_real.origen_id.id not in [7,22,23] and getYMDdate(lectura_real.name)<getYMDdate(lectura.data_actual)], reverse=True, key=lambda l:l.name)
                    if len(lectura_real)>0:
                        lectures_real_c[lectura.comptador].append((lectura.name[-3:-1],val(lectura_real[0].lectura),dateformat(lectura_real[0].name)))

        total_lectures_a = dict([(p, 0) for p in periodes_a])
        total_lectures_r = dict([(p, 0) for p in periodes_r])
        total_lectures_c = dict([(p, 0) for p in periodes_c])
        total_lectures_g = dict([(p, 0) for p in periodes_g])

        for c, ls in lectures_a.items():
            for l in ls:
                total_lectures_a[l[0]] += l[3]

        for c, ls in lectures_r.items():
            for l in ls:
                total_lectures_r[l[0]] += l[3]

        for c, ls in lectures_c.items():
            for l in ls:
                total_lectures_c[l[0]] += l[3]

        for c, ls in lectures_g.items():
            for l in ls:
                total_lectures_g[l[0]] += l[3]

        has_adjust_a = False
        for k,v in lectures_a.items():
            for l in v:
                if l[8] != 0:
                    has_adjust_a = True

        has_readings_g = False
        has_adjust_g = False
        for k,v in lectures_g.items():
            for l in v:
                if l[1] != 0 or  l[2] != 0 :
                    has_readings_g = True
                if l[8] != 0:
                    has_adjust_g = True

        return {
            'periodes_a': periodes_a,
            'periodes_r': periodes_r,
            'periodes_c': periodes_c,
            'periodes_g': periodes_g,
            'lectures_a': lectures_a,
            'lectures_r': lectures_r,
            'lectures_c': lectures_c,
            'lectures_g': lectures_g,
            'lectures_real_a': lectures_real_a,
            'lectures_real_r': lectures_real_r,
            'lectures_real_c': lectures_real_c,
            'lectures_real_g': lectures_real_g,
            'total_lectures_a': total_lectures_a,
            'total_lectures_r': total_lectures_r,
            'total_lectures_c': total_lectures_c,
            'total_lectures_g': total_lectures_g,
            'has_adjust_a': has_adjust_a,
            'has_adjust_g' : has_adjust_g,
            'has_readings_g': has_readings_g,
        }