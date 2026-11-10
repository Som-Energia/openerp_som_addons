# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
import binascii
import csv

from osv import osv, fields
from tools.translate import _
from ..models.report_test import RES_INTERPRETER
from .report_test_csv import read_test_csv, write_test_csv


class WizardReportTestGroupCsv(osv.osv_memory):
    _name = 'wizard.report.test.group.csv'

    def _default_group(self, cursor, uid, context=None):
        context = context or {}
        if context.get('active_model') != 'report.test.group':
            return False
        group_ids = context.get('active_ids') or [context.get('active_id')]
        return group_ids[0] if len(group_ids) == 1 else False

    def _resolve_report(self, cursor, uid, row, default_report, cache, context=None):
        report_name = row.get('report_name', '').strip()
        report_model = row.get('report_model', '').strip()
        if not report_name:
            if not default_report:
                raise ValueError('Seleccioneu un report per defecte o indiqueu report_name al CSV.')
            if report_model and default_report.model != report_model:
                raise ValueError('report_model no coincideix amb el model del report per defecte.')
            return default_report.id
        key = (report_name, report_model)
        if key not in cache:
            domain = [('report_name', '=', report_name)]
            if report_model:
                domain.append(('model', '=', report_model))
            report_ids = self.pool.get('ir.actions.report.xml').search(
                cursor, uid, domain, limit=2, context=context
            )
            if len(report_ids) != 1:
                raise ValueError(
                    "El report '{}' no existeix o és ambigu; reviseu report_model.".format(
                        report_name
                    )
                )
            cache[key] = report_ids[0]
        return cache[key]

    def _prepare_test(self, cursor, uid, row, wizard, priority, cache, context=None):
        value = row['value'].strip()
        interpreter = row.get('interpreter', '').strip() or wizard.interpreter
        if interpreter not in dict(RES_INTERPRETER):
            raise ValueError('Interpretador desconegut: {}.'.format(interpreter))
        if not value or len(value) > 64:
            raise ValueError("La columna 'value' ha de contenir entre 1 i 64 caràcters.")
        if interpreter == 'id':
            try:
                valid_id = int(value) > 0
            except ValueError:
                valid_id = False
            if not valid_id:
                raise ValueError('Un ID directe ha de ser un nombre enter positiu.')
        name = row.get('name', '').strip() or '{}: {}'.format(interpreter, value)[:64]
        if len(name) > 64:
            raise ValueError("La columna 'name' no pot superar els 64 caràcters.")
        try:
            priority = int(row.get('priority', '').strip() or priority)
        except ValueError:
            raise ValueError("La columna 'priority' ha de ser un nombre enter.")
        active = row.get('active', '').strip().lower()
        if active not in ('', '1', '0', 'true', 'false', 'yes', 'no'):
            raise ValueError("La columna 'active' ha de ser 1, 0, true, false, yes o no.")
        return {
            'name': name,
            'description': row.get('description', ''),
            'priority': priority,
            'active': active not in ('0', 'false', 'no'),
            'report': self._resolve_report(
                cursor, uid, row, wizard.report, cache, context=context
            ),
            'interpreter': interpreter,
            'value': value,
            'result': 'pending',
        }

    def import_csv(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context=context)
        if wizard.state != 'init':
            return True
        group_id = wizard.group_id.id if wizard.group_id else False
        group_name = (wizard.group_name or '').strip()
        if not group_id and (not group_name or len(group_name) > 64):
            raise osv.except_osv(
                _('Importació de CSV'),
                _('Indiqueu un nom per al nou grup (entre 1 i 64 caràcters).')
            )
        if not wizard.csv_file:
            raise osv.except_osv(_('Importació de CSV'), _('Carregueu un fitxer CSV.'))
        test_obj = self.pool.get('report.test')
        priority = 0
        if group_id:
            previous = test_obj.search(
                cursor, uid, [('group_id', '=', group_id)],
                order='priority DESC', limit=1, context={'active_test': False}
            )
            if previous:
                priority = test_obj.read(cursor, uid, previous[0], ['priority'])['priority']
        line = None
        try:
            content = base64.b64decode(wizard.csv_file)
            rows = read_test_csv(content)
            prepared = []
            cache = {}
            for line, row in rows:
                values = self._prepare_test(
                    cursor, uid, row, wizard, priority + 10, cache, context=context
                )
                priority = max(priority, values['priority'])
                prepared.append(values)
        except (UnicodeError, csv.Error, binascii.Error):
            raise osv.except_osv(
                _('Importació de CSV'),
                _("No s'ha pogut llegir el fitxer CSV. "
                  "Reviseu-ne el format i torneu-lo a carregar.")
            )
        except ValueError as error:
            message = u'{}'.format(error)
            if line is not None:
                message = _('Línia {} del CSV: {}').format(line, message)
            raise osv.except_osv(_('Importació de CSV'), message)

        if not group_id:
            group_id = self.pool.get('report.test.group').create(cursor, uid, {
                'name': group_name, 'priority': 100,
            }, context=context)
        for values in prepared:
            values['group_id'] = group_id
            test_obj.create(cursor, uid, values, context=context)
        self.write(cursor, uid, ids, {
            'group_id': group_id,
            'state': 'end',
            'info': _("S'han importat {} tests. No s'han modificat els tests existents.").format(
                len(prepared)
            ),
        }, context=context)
        return True

    def export_csv(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context=context)
        if not wizard.group_id:
            raise osv.except_osv(
                _('Exportació de CSV'), _('Seleccioneu el grup que voleu exportar.')
            )
        test_obj = self.pool.get('report.test')
        export_context = dict(context or {}, active_test=False)
        test_ids = test_obj.search(
            cursor, uid, [('group_id', '=', wizard.group_id.id)],
            order='priority,id', context=export_context
        )
        rows = []
        for test in test_obj.browse(cursor, uid, test_ids, context=export_context):
            rows.append({
                'name': test.name,
                'description': test.description or '',
                'priority': test.priority,
                'active': '1' if test.active else '0',
                'report_name': test.report.report_name,
                'report_model': test.report.model,
                'interpreter': test.interpreter,
                'value': test.value,
            })
        self.write(cursor, uid, ids, {
            'output_file': base64.b64encode(write_test_csv(rows)),
            'output_filename': 'report_tests_{}.csv'.format(wizard.group_id.id),
            'state': 'end',
            'info': _("S'han exportat {} tests, sense PDF adjunts ni resultats d'execució.").format(
                len(rows)
            ),
        }, context=context)
        return True

    def open_group(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Grup de tests de reports'),
            'res_model': 'report.test.group',
            'res_id': wizard.group_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'active_test': False},
        }

    _columns = {
        'state': fields.selection([('init', 'Inicial'), ('end', 'Finalitzat')], 'Estat'),
        'operation': fields.selection(
            [('import', 'Importació'), ('export', 'Exportació')], 'Operació'
        ),
        'group_id': fields.many2one(
            'report.test.group', 'Grup existent',
            help='La importació afegeix tests a aquest grup. Deixeu-lo buit per crear un grup nou.',
        ),
        'group_name': fields.char('Nom del nou grup', size=64),
        'report': fields.many2one(
            'ir.actions.report.xml', 'Report per defecte',
            help='Es fa servir quan una fila del CSV no especifica report_name.',
        ),
        'interpreter': fields.selection(RES_INTERPRETER, 'Interpretació per defecte'),
        'csv_file': fields.binary(
            'Fitxer CSV',
            help='CSV en UTF-8 separat per comes, punts i coma o tabuladors. '
                 'Columna obligatòria: value. '
                 'Columnes opcionals: name, description, priority, active, report_name, '
                 'report_model, '
                 'interpreter.',
        ),
        'csv_filename': fields.char('Nom del fitxer CSV', size=256),
        'output_file': fields.binary('CSV exportat', readonly=True),
        'output_filename': fields.char("Nom del fitxer d'exportació", size=256, readonly=True),
        'info': fields.text('Informació', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'operation': lambda self, cr, uid, ctx: (ctx or {}).get('default_operation', 'import'),
        'group_id': _default_group,
        'interpreter': lambda *a: 'id',
    }


WizardReportTestGroupCsv()
