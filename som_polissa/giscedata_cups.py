# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class GiscedataCupsPs(osv.osv):
    """Classe d'un CUPS (Punt de servei)."""

    _name = "giscedata.cups.ps"
    _inherit = "giscedata.cups.ps"

    _NEW_ORIGENS_CONANY = [
        ("consums", _(u"5_Historic consums")),
        ("factures", _(u"4_Historic factures")),
        ("pdf", _(u"1_Consum 12 mesos")),
        ("consums_periods", _(u"3_> 12 factures: Historic consums per periodes")),
        ("estadistic", _(u"1000_< 3 factures: Estadística SOM")),
        ("usuari", _(u"100_usuari (webforms)")),
        ("cnmc", _(u"500_Entre 3 i 12 factures: Estadística CNMC")),
    ]

    def __init__(self, pool, cursor):
        """Afegim els nou orígen"""
        super(GiscedataCupsPs, self).__init__(pool, cursor)
        origens = self.get_fonts_consums_anuals(cursor, 1)
        for origen in origens:
            current_sel = dict(self._columns["conany_origen"].selection).keys()
            if origen["origen"] not in current_sel:
                new_sel = (
                    origen["origen"],
                    dict(self._NEW_ORIGENS_CONANY).get(origen["origen"], origen["origen"]),
                )
                self._columns["conany_origen"].selection.append(new_sel)

    def get_fonts_consums_anuals(self, cursor, uid, context=None):
        """Afegim consum_anual_consum_lectures com a font de consum anual"""
        llista = super(GiscedataCupsPs, self).get_fonts_consums_anuals(cursor, uid, context=context)

        for i in range(len(llista)):
            if llista[i]["func"] == "get_consum_anual_lectures":
                del llista[i]
                break

        vals = [
            {
                "priority": 5,
                "model": "giscedata.polissa",
                "func": "get_consum_anual_consum_lectures",
                "origen": "consums",
            },
            {
                "priority": 4,
                "model": "giscedata.polissa",
                "func": "get_consum_anual_factures",
                "origen": "factures",
            },
            {
                "priority": 1,
                "model": "giscedata.polissa",
                "func": "get_consum_anual_pdf",
                "origen": "pdf",
                "periods": True,
            },
            {
                "priority": 100,
                "model": "giscedata.polissa",
                "func": "get_consum_anual_webforms",
                "origen": "usuari",
            },
            {
                "priority": 3,
                "model": "giscedata.polissa",
                "func": "get_consum_anual_backend_gisce",
                "origen": "consums_periods",
                "periods": True,
            },
            {
                "priority": 500,
                "model": "giscedata.polissa",
                "func": "get_consum_prorrageig_cnmc",
                "origen": "cnmc",
                "periods": True,
            },
            {
                "priority": 1000,
                "model": "giscedata.polissa",
                "func": "get_consum_anual_estadistic_som",
                "origen": "estadistic",
                "periods": True,
            },
        ]

        llista += vals

        return llista

    _columns = {
        'importacio_cadastre_incidencies_origen': fields.char(
            'Incidència Origen Importació', size=128),
    }


GiscedataCupsPs()
