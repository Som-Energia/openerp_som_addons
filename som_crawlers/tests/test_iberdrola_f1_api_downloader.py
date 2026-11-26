# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime
import io
from itertools import product
import json
import os
import shutil
import tempfile
import zipfile

import mock
import requests
from destral import testing
from destral.transaction import Transaction

from som_crawlers.api_downloaders import get_instance_from_api_module
from som_crawlers.api_downloaders.iberdrola_f1 import Iberdrola_F1
from som_crawlers.models.exceptions import (
    CrawlingLoginException, CrawlingProcessException, NoResultsException,
)
from .test_iberdrola_api_downloaders import IberdrolaConfig


class IberdrolaF1ApiDownloaderTests(testing.OOTestCase):
    def setUp(self):
        self.config = IberdrolaConfig()
        self.downloader = Iberdrola_F1(self.config)
        self.addCleanup(self.downloader.session.close)
        self.working_directory = tempfile.mkdtemp(prefix='test-ide-f1-')
        self.addCleanup(shutil.rmtree, self.working_directory)
        self.output_directory = os.path.join(self.working_directory, 'downloads')
        os.mkdir(self.output_directory)
        self.downloader.target_filename = os.path.join(self.output_directory, 'F1.zip')
        self.downloader.get_intervals = mock.Mock(return_value=(
            datetime(2026, 9, 1, 12, 30, 45), datetime(2026, 9, 2, 13, 45, 59),
        ))
        self.request_post = mock.Mock()
        self.downloader.session.post = self.request_post
        self.now = 0
        clock_patch = mock.patch(
            'som_crawlers.api_downloaders.iberdrola_f1._clock',
            side_effect=lambda: self.now,
        )
        self.clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        sleep_patch = mock.patch(
            'som_crawlers.api_downloaders.iberdrola_f1.sleep',
            side_effect=self.advance_time,
        )
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)
        self.zip_content = self.make_zip([
            ('messages/0021_F1_001.xml', b'<Factura>one</Factura>'),
            ('0021_A1_002.xml', b'<Alta/>'),
            ('F1/0021_Q1_003.xml', b'<Q1/>'),
            ('0021_f1_004.XML', b'<Factura>two</Factura>'),
            ('F1.txt', b'not-xml'),
        ])

    def advance_time(self, seconds):
        self.now += seconds

    def response(self, data=None, content=None, status_code=200):
        result = requests.Response()
        result.status_code = status_code
        if content is None:
            result._content = json.dumps(data).encode('utf-8')
            result.headers['Content-Type'] = 'application/json'
        else:
            result._content = content
            result.headers['Content-Type'] = 'application/zip'
        return result

    def make_zip(self, files):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for filename, content in files:
                archive.writestr(filename, content)
        return output.getvalue()

    def ready_responses(self, content=None):
        return [
            self.response({'codigoDescarga': '28282'}),
            self.response({'estado': 'F', 'mensaje': 'Ticket listo para la descarga'}),
            self.response(content=self.zip_content if content is None else content),
        ]

    def assert_failure(self, exception_type):
        with self.assertRaises(exception_type) as error:
            self.downloader.download_files()
        self.assertFalse(os.path.exists(self.downloader.target_filename))
        self.assertEqual(os.listdir(self.output_directory), [])
        self.assertEqual(os.listdir(self.working_directory), ['downloads'])
        return error.exception

    def test_factory_selects_absolute_downloader_for_f1_on_all_three_portals(self):
        for portal, code in (('iberdrola', '0021'), ('conquense', '0032'), ('anselmo', '0118')):
            downloader = get_instance_from_api_module(self.config, portal, process='f1')
            self.addCleanup(downloader.session.close)

            self.assertIsInstance(downloader, Iberdrola_F1)
            self.assertEqual(downloader.name, portal + '_f1')
            self.assertEqual(downloader.cod_portal, code)
            self.assertEqual(downloader.ticket_poll_interval, 60)
            self.assertEqual(downloader.ticket_timeout, 1800)

    def test_all_other_processes_keep_synchronous_downloads_on_all_three_portals(self):
        processes = (
            'a1', 'a3', 'b1', 'b2', 'c1', 'c2', 'd1', 'e1', 'e2',
            'j1', 'm1', 'm2', 'p0', 'q1', 'r0', 'r1', 't1',
        )
        for portal, process in product(('iberdrola', 'conquense', 'anselmo'), processes):
            other = get_instance_from_api_module(self.config, portal, process=process)
            self.addCleanup(other.session.close)
            self.assertNotIsInstance(other, Iberdrola_F1)
            other.session.post = mock.Mock(return_value=self.response(content=self.zip_content))
            other.get_intervals = self.downloader.get_intervals
            other.target_filename = self.downloader.target_filename

            other.download_files()

            request = other.session.post.call_args
            self.assertTrue(request[0][0].endswith('/DescargarMensajesMasivosAPI'))
            self.assertEqual(request[1]['json']['filtros']['proceso'], process.upper())
            with open(other.target_filename, 'rb') as output:
                self.assertEqual(output.read(), self.zip_content)

    def test_full_f1_flow_keeps_portal_codes_and_credentials_separate(self):
        sessions = []
        for portal, code in (('iberdrola', '0021'), ('conquense', '0032'), ('anselmo', '0118')):
            config = IberdrolaConfig()
            config.usuari = portal + '-user'
            config.contrasenya = portal + '-password'
            config.api_key = portal + '-api-key'
            downloader = get_instance_from_api_module(config, portal, process='f1')
            self.addCleanup(downloader.session.close)
            self.assertNotIn(downloader.session, sessions)
            sessions.append(downloader.session)
            downloader.target_filename = self.downloader.target_filename
            downloader.get_intervals = self.downloader.get_intervals
            filename = code + '_F1_001.xml'
            ticket_code = '28' + code
            responses = [
                self.response({
                    'codigo': 'OK', 'descripcion': 'OK', 'jwt': portal + '-jwt',
                    'nombreCookie': 'IDEAUTH', 'tokenSeguridad': portal + '-security-token',
                }),
                self.response({'codigoDescarga': ticket_code}),
                self.response({'estado': 'F'}),
                self.response(content=self.make_zip([
                    (filename, b'<F1/>'), (code + '_A1_001.xml', b'<A1/>'),
                ])),
            ]
            received = []

            def request(url, **kwargs):
                received.append((url, kwargs, dict(downloader.session.headers)))
                return responses.pop(0)

            downloader.session.post = mock.Mock(side_effect=request)

            downloader.start()

            self.assertEqual([call[0] for call in received], [
                config.url_portal + 'LoginAPI',
                config.url_portal + 'API/gmagente/DescargaAbsoluta',
                config.url_portal + 'API/gmagente/ConsultarEstadoTicket',
                config.url_portal + 'ConsultaDescargaAPI',
            ])
            self.assertEqual(received[0][1]['json'], {'codPortal': code})
            self.assertEqual(received[0][1]['auth'].username, config.usuari)
            self.assertEqual(received[0][1]['auth'].password, config.contrasenya)
            self.assertEqual(received[1][1]['json']['agenteSolicitante'], code)
            self.assertEqual(received[2][1]['json'], {'codDescarga': ticket_code})
            self.assertEqual(received[3][1]['json'], {'codDescarga': ticket_code})
            for index, request_data in enumerate(received):
                headers = request_data[2]
                self.assertEqual(headers['Portal'], code)
                self.assertEqual(headers['API-Key'], config.api_key)
                self.assertEqual(headers['User-Agent'], 'portal_agentes')
                if index:
                    self.assertEqual(headers['jwt'], portal + '-jwt')
                    self.assertEqual(headers['IDEAUTH'], portal + '-security-token')
                    self.assertNotIn('auth', request_data[1])
            with zipfile.ZipFile(downloader.target_filename, 'r') as result:
                self.assertEqual(result.namelist(), [filename])
                self.assertEqual(result.read(filename), b'<F1/>')

    def test_complete_flow_creates_ticket_once_waits_and_saves_only_f1(self):
        responses = self.ready_responses()
        responses.insert(1, self.response({
            'estado': 'P', 'mensaje': 'El ticket esta pendiente de ser procesado',
        }))
        self.request_post.side_effect = responses

        self.downloader.download_files()

        self.assertEqual(self.request_post.call_args_list, [
            mock.call(
                self.config.url_portal + 'API/gmagente/DescargaAbsoluta',
                json={
                    'agenteSolicitante': '0021',
                    'fechaDesde': '2026-09-01',
                    'fechaHasta': '2026-09-02',
                    'horaDesde': '12:30:45',
                    'horaHasta': '13:45:59',
                    'filtro': '',
                    'firmado': False,
                    'marcarDescargados': False,
                    'tipoInformacion': 'Pendientes Descargar',
                },
                timeout=300, allow_redirects=False,
            ),
            mock.call(
                self.config.url_portal + 'API/gmagente/ConsultarEstadoTicket',
                json={'codDescarga': '28282'}, timeout=60, allow_redirects=False,
            ),
            mock.call(
                self.config.url_portal + 'API/gmagente/ConsultarEstadoTicket',
                json={'codDescarga': '28282'}, timeout=60, allow_redirects=False,
            ),
            mock.call(
                self.config.url_portal + 'ConsultaDescargaAPI',
                json={'codDescarga': '28282'}, timeout=300, allow_redirects=False,
            ),
        ])
        self.sleep.assert_called_once_with(60)
        with zipfile.ZipFile(self.downloader.target_filename, 'r') as result:
            self.assertEqual(result.namelist(), [
                'messages/0021_F1_001.xml', '0021_f1_004.XML',
            ])
            self.assertEqual(result.read('messages/0021_F1_001.xml'), b'<Factura>one</Factura>')
            self.assertEqual(result.read('0021_f1_004.XML'), b'<Factura>two</Factura>')
            self.assertIsNone(result.testzip())
        self.assertIsNone(self.downloader.ticket_code)
        self.assertEqual(os.listdir(self.output_directory), ['F1.zip'])
        self.assertEqual(os.listdir(self.working_directory), ['downloads'])

    def test_ready_ticket_is_downloaded_without_sleep(self):
        self.request_post.side_effect = self.ready_responses()

        self.downloader.download_files()

        self.assertFalse(self.sleep.called)
        self.assertEqual(self.request_post.call_count, 3)

    def test_all_files_configuration_is_preserved(self):
        self.config.pending_files_only = False
        self.request_post.side_effect = self.ready_responses()

        self.downloader.download_files()

        payload = self.request_post.call_args_list[0][1]['json']
        self.assertEqual(payload['tipoInformacion'], 'Todos')
        self.assertFalse(payload['marcarDescargados'])
        self.assertFalse(payload['firmado'])

    def test_ticket_parser_requires_observed_codigo_descarga_field(self):
        for data in (
            {}, {'codDescarga': '28282'}, {'codigoDescarga': ''},
            {'codigoDescarga': None}, {'codigoDescarga': False},
            {'codigoDescarga': 28282}, {'codigoDescarga': '0'},
            {'codigoDescarga': '28282\n'}, {'codigoDescarga': '../private-detail'},
            {'codigoDescarga': ['28282']}, ['28282'],
        ):
            self.request_post.return_value = self.response(data)

            error = self.assert_failure(CrawlingProcessException)

            self.assertNotIn('private-detail', str(error))
            self.assertIsNone(self.downloader.ticket_code)
        self.assertFalse(self.sleep.called)

    def test_creation_failure_does_not_poll_or_retry(self):
        self.request_post.return_value = self.response(
            content=b'private-server-detail', status_code=500,
        )

        error = self.assert_failure(CrawlingProcessException)

        self.assertIn('HTTP 500', str(error))
        self.assertNotIn('private-server-detail', str(error))
        self.assertEqual(self.request_post.call_count, 1)

    def test_creation_timeout_does_not_automatically_create_another_ticket(self):
        self.request_post.side_effect = requests.Timeout('private-api-key')

        error = self.assert_failure(CrawlingProcessException)

        self.assertNotIn('private-api-key', str(error))
        self.assertEqual(self.request_post.call_count, 1)

    def test_creation_rejects_non_json_response(self):
        self.request_post.return_value = self.response(content=b'<html>private-detail</html>')

        error = self.assert_failure(CrawlingProcessException)

        self.assertNotIn('private-detail', str(error))
        self.assertEqual(self.request_post.call_count, 1)

    def test_waits_for_full_30_minutes_polling_once_per_minute(self):
        pending = [self.response({'estado': 'P'}) for _ in range(30)]
        self.request_post.side_effect = [self.response({'codigoDescarga': '28282'})] + pending

        error = self.assert_failure(CrawlingProcessException)

        self.assertEqual(self.now, 1800)
        self.assertEqual(self.sleep.call_args_list, [mock.call(60)] * 30)
        self.assertEqual(self.request_post.call_count, 31)
        self.assertEqual(self.downloader.ticket_code, '28282')
        self.assertIn('28282', str(error))
        self.assertIn('manualment', str(error))

    def test_ready_ticket_after_29_minutes_is_still_downloaded(self):
        responses = self.ready_responses()
        pending = [self.response({'estado': 'P'}) for _ in range(29)]
        self.request_post.side_effect = responses[:1] + pending + responses[1:]

        self.downloader.download_files()

        self.assertEqual(self.now, 1740)
        self.assertEqual(self.sleep.call_args_list, [mock.call(60)] * 29)
        self.assertEqual(self.request_post.call_count, 32)
        self.assertTrue(os.path.exists(self.downloader.target_filename))
        self.assertIsNone(self.downloader.ticket_code)

    def test_waiting_is_bounded_by_elapsed_time(self):
        self.downloader.ticket_timeout = 15
        self.downloader.ticket_poll_interval = 10
        self.request_post.side_effect = [
            self.response({'codigoDescarga': '28282'}),
            self.response({'estado': 'P'}), self.response({'estado': 'P'}),
        ]

        error = self.assert_failure(CrawlingProcessException)

        self.assertIn('28282', str(error))
        self.assertEqual(self.downloader.ticket_code, '28282')
        self.assertEqual(self.now, 15)
        self.assertEqual(self.sleep.call_args_list, [mock.call(10), mock.call(5)])
        self.assertEqual(self.request_post.call_count, 3)
        self.assertEqual(self.request_post.call_args_list[1][1]['timeout'], 15)
        self.assertEqual(self.request_post.call_args_list[2][1]['timeout'], 5)

    def test_waiting_is_bounded_even_when_clock_moves_backwards(self):
        self.downloader.ticket_max_polls = 3
        self.clock.side_effect = lambda: -self.now
        responses = [self.response({'codigoDescarga': '28282'})]
        responses.extend(self.response({'estado': 'P'}) for _ in range(3))
        self.request_post.side_effect = responses

        self.assert_failure(CrawlingProcessException)

        self.assertEqual(self.request_post.call_count, 4)
        self.assertEqual(self.sleep.call_count, 2)

    def test_late_ready_response_does_not_start_download_after_deadline(self):
        self.downloader.ticket_code = '28282'
        self.downloader.ticket_timeout = 15

        def slow_response(*args, **kwargs):
            self.now += 16
            return self.response({'estado': 'F'})

        self.request_post.side_effect = slow_response

        self.assert_failure(CrawlingProcessException)

        self.assertEqual(self.request_post.call_count, 1)
        self.assertFalse(self.sleep.called)

    def test_unknown_or_error_states_are_not_no_results(self):
        for state in ('E', 'X', None, '', {'private-detail': True}):
            self.downloader.ticket_code = '28282'
            self.request_post.return_value = self.response({
                'estado': state, 'mensaje': 'private-detail',
            })

            error = self.assert_failure(CrawlingProcessException)

            self.assertNotIsInstance(error, NoResultsException)
            self.assertNotIn('private-detail', str(error))
            self.assertEqual(self.downloader.ticket_code, '28282')
        self.assertFalse(self.sleep.called)

    def test_status_rejects_non_json_response(self):
        self.request_post.side_effect = [
            self.response({'codigoDescarga': '28282'}),
            self.response(content=b'<html>private-detail</html>'),
        ]

        error = self.assert_failure(CrawlingProcessException)

        self.assertNotIn('private-detail', str(error))
        self.assertEqual(self.request_post.call_count, 2)

    def test_status_http_403_stops_before_downloading(self):
        self.request_post.side_effect = [
            self.response({'codigoDescarga': '28282'}),
            self.response(content=b'', status_code=403),
        ]

        self.assert_failure(CrawlingLoginException)

        self.assertEqual(self.request_post.call_count, 2)
        self.assertEqual(self.downloader.ticket_code, '28282')

    def test_retry_on_same_instance_reuses_ticket_after_timeout(self):
        self.downloader.ticket_max_polls = 1
        self.request_post.side_effect = [
            self.response({'codigoDescarga': '28282'}), self.response({'estado': 'P'}),
        ]
        self.assert_failure(CrawlingProcessException)
        self.request_post.reset_mock()
        self.request_post.side_effect = self.ready_responses()[1:]

        self.downloader.download_files()

        self.assertEqual(self.request_post.call_count, 2)
        self.assertTrue(self.request_post.call_args_list[0][0][0].endswith(
            '/ConsultarEstadoTicket'
        ))
        self.assertIsNone(self.downloader.ticket_code)

    def test_download_http_500_does_not_publish_zip(self):
        responses = self.ready_responses()
        responses[-1] = self.response(content=b'private-detail', status_code=500)
        self.request_post.side_effect = responses

        error = self.assert_failure(CrawlingProcessException)

        self.assertIn('HTTP 500', str(error))
        self.assertNotIn('private-detail', str(error))
        self.assertEqual(self.downloader.ticket_code, '28282')

    def test_invalid_zip_does_not_publish_or_discard_ticket(self):
        self.request_post.side_effect = self.ready_responses(content=b'PK-invalid')

        self.assert_failure(CrawlingProcessException)

        self.assertEqual(self.downloader.ticket_code, '28282')

    def test_empty_zip_is_no_results_and_completes_ticket(self):
        self.request_post.side_effect = self.ready_responses(content=self.make_zip([]))

        self.assert_failure(NoResultsException)

        self.assertIsNone(self.downloader.ticket_code)

    def test_zip_without_f1_is_no_results(self):
        content = self.make_zip([
            ('A1.xml', b'<A1/>'), ('Q1.xml', b'<Q1/>'),
            ('F1/A3.xml', b'<A3/>'), ('F1.txt', b'not XML'),
        ])
        self.request_post.side_effect = self.ready_responses(content=content)

        self.assert_failure(NoResultsException)

        self.assertIsNone(self.downloader.ticket_code)

    def test_filter_matches_filename_not_unix_or_windows_parent_directory(self):
        content = self.make_zip([
            ('F1/other.xml', b'<Other/>'), ('F1\\other.xml', b'<Other/>'),
            ('other/0021_F1.xml', b'<F1/>'), ('other\\0021_f1.XML', b'<F1/>'),
            ('F1.zip', b'not XML'), ('F1.xml/', b''),
        ])

        filtered = self.downloader._filter_f1_zip(content)

        with zipfile.ZipFile(io.BytesIO(filtered), 'r') as result:
            self.assertEqual(result.namelist(), [
                'other/0021_F1.xml', 'other\\0021_f1.XML',
            ])

    def test_absolute_download_can_contain_more_than_1000_f1_files(self):
        content = self.make_zip([
            ('0021_F1_{:04d}.xml'.format(index), b'<F1/>') for index in range(1001)
        ])
        self.request_post.side_effect = self.ready_responses(content=content)

        self.downloader.download_files()

        with zipfile.ZipFile(self.downloader.target_filename, 'r') as result:
            self.assertEqual(len(result.infolist()), 1001)

    def test_existing_output_is_preserved_if_no_f1_files_are_found(self):
        with open(self.downloader.target_filename, 'wb') as output:
            output.write(b'previous-content')
        self.request_post.side_effect = self.ready_responses(content=self.make_zip([
            ('A1.xml', b'<A1/>'),
        ]))

        with self.assertRaises(NoResultsException):
            self.downloader.download_files()

        with open(self.downloader.target_filename, 'rb') as output:
            self.assertEqual(output.read(), b'previous-content')

    def test_existing_erp_download_step_only_receives_filtered_f1_zip(self):
        pool = self.openerp.pool
        data_obj = pool.get('ir.model.data')
        step_obj = pool.get('som.crawlers.task.step')
        login = self.response({
            'codigo': 'OK', 'descripcion': 'OK', 'jwt': 'login-jwt',
            'nombreCookie': 'IDEAUTH', 'tokenSeguridad': 'security-token',
        })
        self.request_post.side_effect = [login] + self.ready_responses()

        def attach_filtered_zip(*args, **kwargs):
            with zipfile.ZipFile(self.downloader.target_filename, 'r') as result:
                self.assertEqual(result.namelist(), [
                    'messages/0021_F1_001.xml', '0021_f1_004.XML',
                ])
            return 'filtered ZIP ready for attachment'

        with Transaction().start(self.database) as txn:
            step_id = data_obj.get_object_reference(
                txn.cursor, txn.user, 'som_crawlers', 'pas_descarregar_iberdrola_api_f1'
            )[1]
            result_id = data_obj.get_object_reference(
                txn.cursor, txn.user, 'som_crawlers', 'demo_result_1'
            )[1]
            with mock.patch(
                'som_crawlers.models.som_crawlers_task_step.get_instance_from_api_module',
                return_value=self.downloader,
            ) as factory, mock.patch.object(
                step_obj, 'attach_files_zip', side_effect=attach_filtered_zip,
            ) as attach:
                result = step_obj.download_api_files(
                    txn.cursor, txn.user, step_id, result_id,
                )

            factory.assert_called_once_with(
                mock.ANY, 'iberdrola', 'f1', retailer_cdos=mock.ANY,
            )
            self.assertEqual(attach.call_count, 1)
            self.assertEqual(result, 'filtered ZIP ready for attachment')
            result_data = pool.get('som.crawlers.result').read(
                txn.cursor, txn.user, result_id, ['resultat_bool']
            )
            self.assertTrue(result_data['resultat_bool'])

    def test_erp_task_without_f1_does_not_attach_or_import_existing_output(self):
        pool = self.openerp.pool
        data_obj = pool.get('ir.model.data')
        task_obj = pool.get('som.crawlers.task')
        step_obj = pool.get('som.crawlers.task.step')
        with open(self.downloader.target_filename, 'wb') as output:
            output.write(b'previous-content')
        login = self.response({
            'codigo': 'OK', 'descripcion': 'OK', 'jwt': 'login-jwt',
            'nombreCookie': 'IDEAUTH', 'tokenSeguridad': 'security-token',
        })
        content = self.make_zip([('A1.xml', b'<A1/>')])
        self.request_post.side_effect = [login] + self.ready_responses(content=content)

        with Transaction().start(self.database) as txn:
            task_id = data_obj.get_object_reference(
                txn.cursor, txn.user, 'som_crawlers', 'descargar_iberdrola_api_f1'
            )[1]
            with mock.patch(
                'som_crawlers.models.som_crawlers_task_step.get_instance_from_api_module',
                return_value=self.downloader,
            ), mock.patch.object(step_obj, 'attach_files_zip') as attach, mock.patch.object(
                step_obj, 'import_xml_files',
            ) as import_files, mock.patch.object(task_obj, 'schedule_next_execution'):
                task_obj.executar_tasca(txn.cursor, txn.user, task_id)

            self.assertEqual(self.request_post.call_count, 4)
            self.assertFalse(attach.called)
            self.assertFalse(import_files.called)
            result_obj = pool.get('som.crawlers.result')
            result_id = result_obj.search(
                txn.cursor, txn.user, [('task_id', '=', task_id)],
                order='id desc', limit=1,
            )[0]
            result = result_obj.read(
                txn.cursor, txn.user, result_id, ['resultat_bool', 'resultat_text']
            )
            self.assertTrue(result['resultat_bool'])
            self.assertIn('SENSE RESULTATS:', result['resultat_text'])
            with open(self.downloader.target_filename, 'rb') as output:
                self.assertEqual(output.read(), b'previous-content')

    def test_complete_start_renews_jwt_and_closes_session(self):
        login = self.response({
            'codigo': 'OK', 'descripcion': 'OK', 'jwt': 'login-jwt',
            'nombreCookie': 'IDEAUTH', 'tokenSeguridad': 'security-token',
        })
        responses = self.ready_responses()
        responses[0].headers['jwt'] = 'ticket-jwt'
        responses[1].headers['jwt'] = 'status-jwt'
        responses[2].headers['jwt'] = 'download-jwt'
        responses.insert(0, login)
        received_jwts = []

        def request(*args, **kwargs):
            received_jwts.append(self.downloader.session.headers.get('jwt'))
            return responses.pop(0)

        self.request_post.side_effect = request
        self.downloader.session.close = mock.Mock()

        self.downloader.start()

        self.assertEqual(received_jwts, [None, 'login-jwt', 'ticket-jwt', 'status-jwt'])
        self.assertEqual(self.downloader.session.headers['jwt'], 'download-jwt')
        self.assertEqual(self.downloader.session.headers['API-Key'], self.config.api_key)
        self.assertEqual(self.downloader.session.headers['User-Agent'], 'portal_agentes')
        self.downloader.session.close.assert_called_once_with()
