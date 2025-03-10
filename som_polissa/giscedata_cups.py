# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


TABLA_113_dict = {  # Table extracted from gestionatr.defs TABLA_113, not imported due translations issues  # noqa: E501
    '00': _(u"Sense Autoconsum"),   # noqa: E501
    '31': _(u"Sense Excedents Individual - Consum"),
    '32': _(u"Sense Excedents Col·lectiu - Consum"),
    '33': _(u"Sense Excedents Col·lectiu amb acord de compensació – Consum"),
    '41': _(u"Amb excedents i compensació Individual-Consum"),
    '42': _(u"Amb excedents i compensació Col·lectiu-Consum"),
    '43': _(u"Amb excedents i compensació Col·lectiu a través de xarxa - Consum"),
    '51': _(u"Amb excedents sense compensació Individual sense cte. de Serv. Aux. en Xarxa Interior - Consum"),  # noqa: E501
    '52': _(u"Amb excedents sense compensació Col·lectiu sense cte. de Serv. Aux. en Xarxa Interior - Consum"),  # noqa: E501
    '53': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. en Xarxa Interior - Consum"),  # noqa: E501
    '54': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. en Xarxa Interior - Serv. Aux."),  # noqa: E501
    '55': _(u"Amb excedents sense compensació Col·lectiu / en Xarxa Interior - Consum"),
    '56': _(u"Amb excedents sense compensació Col·lectiu / en Xarxa Interior - Serv. Aux."),
    '57': _(u"Amb excedents sense compensació Col·lectiu sense cte de Serv. Aux. (menyspreable) en Xarxa Interior – Consum')"),  # noqa: E501
    '58': _(u"Amb excedents sense compensació Col·lectiu sense cto de Serv. Aux. a través de xarxa - Consum')"),  # noqa: E501
    '61': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. a través de xarxa - Consum"),  # noqa: E501
    '62': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. a través de xarxa - Serv. Aux."),  # noqa: E501
    '63': _(u"Amb excedents sense compensació Col·lectiu a través de xarxa - Consum"),
    '64': _(u"Amb excedents sense compensació Col·lectiu a través de xarxa - Serv. Aux."),
    '71': _(u"Amb excedents sense compensació Individual amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Consum"),  # noqa: E501
    '72': _(u"Amb excedents sense compensació individual amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Serv. Aux."),  # noqa: E501
    '73': _(u"Amb excedents sense compensació Col·lectiu amb cte. de Serv. Aux. a través de xarxa i xarxa interior - Consum"),  # noqa: E501
    '74': _(u"Amb excedents sense compensació Col·lectiu amb cte. de Serv. Aux. a través de xarxa i xarxa interior - SSAA"),  # noqa: E501
}


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
