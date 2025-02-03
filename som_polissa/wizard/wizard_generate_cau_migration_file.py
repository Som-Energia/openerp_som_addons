# -*- encoding: utf-8 -*-
import zipfile
from datetime import datetime
from addons import get_module_resource
from tools.translate import _
from osv import osv, fields

try:
    from StringIO import StringIO  ## for Python 2
except ImportError:
    from io import StringIO  ## for Python 3
import csv
import base64

VERSION_SELECTION = [
    ('VersionInicial', 'Versió Inicial'),
    ('VersionIntermedia', 'Versió Intermitja'),
    ('VersionFinal', 'Versió Final')
]

MAPPING_SUBSECCION = {
    'aa': '10',
    'a0': '21',
    'b1': '20',
    'b2': '20',
    '10': '10',
    '11': '11',
    '20': '20',
    '21': '21',
    '00': '00',
    '0C': '0C',
}


class WizardGenerateCAUMigrationFile(osv.osv_memory):
    """Genera un Fitxer amb el format definit per la CNMC amb la informació per a les comers
    de cares a la migració dels autoconsums existents."""

    _name = 'wizard.generate.cau.migration.file'

    def _get_default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cursor, uid, uid, context=context)
        ree_code = user.company_id.partner_id.ref
        data_publicacio = datetime.now().strftime('%Y%m%d')

        text = _("Es generarà un fitxer amb els autoconsums disponibles al sistema vinculats "
                 "a CUPS a dia d'avui en el format establert per la CNMC. Es generarà un fitxer "
                 "per distribuïdora. El nom del fitxer resultant tindrà un prefix amb el codi "
                 "REE de la distribuïdora per a poder identificar-la fàcil i contrastar el "
                 "fitxer."
                 ).format(ree_code, data_publicacio, ree_code, data_publicacio)
        return text

    def get_all_autoconsum_data(self, cursor, uid, context=None):
        """ Obté les dades dels autoconsums disponibles al sistema
        """

        if not context:
            context = {}

        res = {}

        today = datetime.now().strftime('%Y-%m-%d')
        autoconsums_query = get_module_resource(
            'som_polissa', 'sql', 'fitxer_migracio_autoconsums.sql'
        )
        sql = open(autoconsums_query).read()
        cursor.execute(sql, {
            'data_inici': today,
            'data_final': today,
        })
        results = cursor.dictfetchall()

        for record in results:
            codi_distri = record['codi_distri']
            if codi_distri not in res:
                res[codi_distri] = {}
            cups = record['cups']
            if cups not in res[codi_distri]:
                res[codi_distri][cups] = {}
            cau = record['cau']
            if cau not in res[codi_distri][cups]:
                nou_comptador_cau = len(res[codi_distri][cups].keys()) + 1
                datos_cau_x = 'DatosCAU_{}'.format(nou_comptador_cau)
                res[codi_distri][cups][cau] = {
                    'DatosCAU_x': datos_cau_x,
                    'generadors': {}
                }

            tipus_auto = ('11' if record['tipoautoconsumo'] in ['31', '32', '33']
                          else '00' if record['tipoautoconsumo'] == '00'
                          else '12')
            res[codi_distri][cups][cau].update({
                'TipoAutoconsumo': tipus_auto,
                'TipoSubseccion': MAPPING_SUBSECCION[record['tiposubseccion']],
                'Colectivo': 'S' if record['colectivo'] else 'N',
            })

            cil = record['cil']
            other_unknown_gens = [g for g in res[codi_distri][cups][cau].keys() if 'unknown' in g]
            gen = cil or 'unknown_gen_{}'.format(len(other_unknown_gens) + 1)
            if not cil or gen not in res[codi_distri][cups][cau]['generadors']:
                nou_comptador_gen = len(res[codi_distri][cups][cau]['generadors'].keys()) + 1
                datos_inst_gen_y = 'DatosInstGen_{}'.format(nou_comptador_gen)
                res[codi_distri][cups][cau]['generadors'][gen] = {'DatosInstGen_y': datos_inst_gen_y}

            res[codi_distri][cups][cau]['generadors'][gen].update({
                'CIL': record['cil'],
                'TecGenerador': record['tecgenerador'],
                'Combustible': record['combustible'],
                'PotInstaladaGen': record['potinstaladagen'] * 1000 if record['potinstaladagen'] else 0,
                'TipoInstalacion': record['tipoinstalacion'],
                'EsquemaMedida': record['esquemamedida'],
                'SSAA': record['ssaa'],
                'UnicoContrato': 'N' if record['ssaa'] == 'S' else 'N',
            })
        return res

    def generar_fitxer(self, cursor, uid, ids, context=None):
        """genera un csv amb les dades dels autoconsums disponibles al sistema
        """

        if not context:
            context = {}

        wiz = self.browse(cursor, uid, ids[0])

        user = self.pool.get('res.users').browse(cursor, uid, uid, context)
        ree_code = user.company_id.partner_id.ref
        versio = wiz.versio or 'VersionInicial'
        data_publicacio = datetime.now().strftime('%Y%m%d')

        headers = [
            'CUPS', 'DatosCAU_x', 'CAU', 'TipoAutoconsumo', 'TipoSubseccion', 'Colectivo',
            'DatosInstGen_y', 'CIL', 'TecGenerador', 'Combustible', 'PotInstaladaGen',
            'TipoInstalacion', 'EsquemaMedida', 'SSAA', 'UnicoContrato'
        ]

        files = []
        autoconsums_data = self.get_all_autoconsum_data(cursor, uid, context=context)
        for distri_code, auto_data_per_distri in autoconsums_data.items():
            linies = [headers]
            for cups, auto_data_per_cups in auto_data_per_distri.items():
                for cau, cau_data in auto_data_per_cups.items():
                    for gen_name, gen_data in cau_data['generadors'].items():
                        linia = []
                        for header in headers:
                            if header == 'CUPS':
                                valor = cups
                            elif header == 'CAU':
                                valor = cau
                            elif header == 'CIL':
                                valor = gen_name if 'unknown' not in gen_name else ''
                            else:
                                valor = gen_data.get(header) or cau_data.get(header)
                            linia.append(valor)
                        linies.append(linia)

            output = StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_NONE)
            for line in linies:
                writer.writerow(line)
            file = base64.b64encode(output.getvalue())
            file_name = '{}_{}_{}_{}.csv'.format(
                distri_code or '9999', ree_code, data_publicacio, versio
            )
            files.append((file, file_name))
            output.close()

        zip_io = StringIO()
        with zipfile.ZipFile(zip_io, 'w') as myzip:
            for f in files:
                myzip.writestr(f[1], base64.b64decode(f[0]))
            myzip.close()
            wiz.write({
                'file': base64.b64encode(zip_io.getvalue()),
                'filename': 'Migracio_autos.zip',
                'state': 'done'
            })

    _columns = {
        'info': fields.text(u'Info', readonly=True),
        'file': fields.binary(u'Fitxer'),
        'filename': fields.text(u'Nom del fitxer'),
        'versio': fields.selection(VERSION_SELECTION, 'Versió del fitxer'),
        'state': fields.selection([('init', 'Init'), ('done', 'Done')], u'State'),
    }

    _defaults = {
        'info': _get_default_info,
        'state': lambda *a: 'init',
        'versio': lambda *a: 'VersionInicial',
    }


WizardGenerateCAUMigrationFile()
