# -*- coding: utf-8 -*-

import tools
import base64
import csv
import StringIO

from osv import osv, fields
from datetime import datetime


HEADERS = [
    "categoria",
    "municipi",
    "num_soci",
    "nif",
    "email",
    "nom",
    "provincia",
    "codi_postal",
    "idioma",
    "comarca",
    "comunitat_autonoma",
]


class WizardLlistatSocis(osv.osv_memory):
    """Assistent per generar un llistat de Socis en CSV"""

    _name = "wizard.llistat.socis"

    _sqlfile = "%s/som_polissa_soci/sql/llistat_socis.sql" % tools.config["addons_path"]

    _query = open(_sqlfile).read()

    def action_genera_csv(self, cursor, uid, ids, context=None):
        """Consulta els socis"""
        wizard = self.browse(cursor, uid, ids[0], context)

        cursor.execute(self._query)
        llistat = cursor.fetchall()

        output = StringIO.StringIO()
        writer = csv.writer(output, delimiter=",")
        writer.writerow(HEADERS)

        for row in llistat:
            tmp = [isinstance(t, basestring) and t.encode("utf-8") or t for t in row]
            writer.writerow(tmp)

        mfile = base64.b64encode(output.getvalue())

        filename = "som_socis_%s.csv" % datetime.strftime(datetime.today(), u"%Y%m%d")

        wizard.write({"name": filename, "file": mfile, "state": "done"})

    _columns = {
        "name": fields.char("Nom fitxer", size=32),
        "state": fields.char("State", size=16),
        "file": fields.binary("Fitxer"),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardLlistatSocis()
