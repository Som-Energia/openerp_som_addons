# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime
import io
import os
import shutil
import tempfile
import zipfile

import mock
import requests
from destral import testing

from som_crawlers.api_downloaders import get_instance_from_api_module
from som_crawlers.api_downloaders.iberdrola import Iberdrola
from som_crawlers.models.exceptions import (
    CrawlingLoginException, CrawlingProcessException, NoResultsException,
)


class IberdrolaConfig(object):
    url_portal = "https://www.i-de.es/pwelconq/services/arq/"
    usuari = "api-user"
    contrasenya = "api-password"
    api_key = "test-api-key"
    pending_files_only = True
    days_of_margin = 7


class IberdrolaApiDownloadersTests(testing.OOTestCase):
    def setUp(self):
        self.config = IberdrolaConfig()
        self.downloader = Iberdrola(self.config)
        self.addCleanup(self.downloader.session.close)
        self.working_directory = tempfile.mkdtemp(prefix='test-ide-')
        self.addCleanup(shutil.rmtree, self.working_directory)
        self.output_directory = os.path.join(self.working_directory, 'downloads')
        os.mkdir(self.output_directory)
        self.downloader.target_filename = os.path.join(self.output_directory, 'result.zip')
        self.downloader.get_intervals = mock.Mock(
            return_value=(datetime(2025, 12, 1), datetime(2025, 12, 31))
        )
        self.request_post = mock.Mock()
        self.downloader.session.post = self.request_post
        self.login_data = {
            "codigo": "OK",
            "descripcion": "OK",
            "jwt": "jwt-token",
            "nombreCookie": "token-name",
            "tokenSeguridad": "security-token",
        }
        self.request_post.return_value = self.make_response()

    def make_response(self, status_code=200, data=None):
        response = mock.Mock(status_code=status_code, headers={})
        response.json.return_value = self.login_data if data is None else data
        return response

    def make_zip(self, files=None, compression=zipfile.ZIP_STORED):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression) as archive:
            for filename, content in files or []:
                archive.writestr(filename, content)
        return output.getvalue()

    def set_download_response(self, content, status_code=200,
                              content_type='application/zip'):
        response = requests.Response()
        response.status_code = status_code
        response._content = content
        response.headers['Content-Type'] = content_type
        self.request_post.return_value = response
        return response

    def assert_download_failure(self, exception_type):
        with self.assertRaises(exception_type) as error:
            self.downloader.download_files()
        self.assertFalse(os.path.exists(self.downloader.target_filename))
        self.assertEqual(os.listdir(self.output_directory), [])
        self.assertEqual(os.listdir(self.working_directory), ['downloads'])
        return error.exception

    def test_factory_accepts_optional_downloader_arguments(self):
        downloader = get_instance_from_api_module(
            self.config, "iberdrola", process="c2", retailer_cdos="0762"
        )
        self.addCleanup(downloader.session.close)

        self.assertEqual(downloader.name, "iberdrola_c2")
        self.assertEqual(downloader.process, "C2")

    def test_login_uses_documented_headers(self):
        self.downloader.login()

        self.request_post.assert_called_once_with(
            self.config.url_portal + "LoginAPI",
            json={"codPortal": "0021"},
            auth=mock.ANY,
            headers={"Accept": "application/json"},
            timeout=60,
            allow_redirects=False,
        )
        auth = self.request_post.call_args[1]['auth']
        self.assertEqual(auth.username, self.config.usuari)
        self.assertEqual(auth.password, self.config.contrasenya)
        session_headers = self.downloader.session.headers
        self.assertEqual(session_headers['API-Key'], self.config.api_key)
        self.assertEqual(session_headers['User-Agent'], 'portal_agentes')
        self.assertEqual(session_headers['Portal'], '0021')
        self.assertEqual(session_headers['jwt'], 'jwt-token')
        self.assertEqual(session_headers['NOMBRETOKEN'], 'token-name')
        self.assertEqual(session_headers['IDEAUTH'], 'security-token')

    def test_session_keeps_common_headers_on_subsequent_requests(self):
        self.downloader.login()
        request = requests.Request('POST', self.config.url_portal + 'example')
        prepared = self.downloader.session.prepare_request(request)

        self.assertEqual(prepared.headers['API-Key'], self.config.api_key)
        self.assertEqual(prepared.headers['User-Agent'], 'portal_agentes')
        self.assertEqual(prepared.headers['jwt'], 'jwt-token')
        self.assertNotIn('Authorization', prepared.headers)

    def test_login_rejects_missing_api_key_before_http_request(self):
        self.config.api_key = False

        with self.assertRaises(CrawlingLoginException):
            self.downloader.login()

        self.assertFalse(self.request_post.called)

    def test_login_rejects_http_errors(self):
        self.request_post.return_value = self.make_response(status_code=401)

        with self.assertRaises(CrawlingLoginException):
            self.downloader.login()

    def test_login_rejects_application_error_with_http_200(self):
        self.request_post.return_value = self.make_response(data={
            'codigo': 'ERROR', 'descripcion': 'Error de autenticacion',
        })

        with self.assertRaises(CrawlingLoginException):
            self.downloader.login()

    def test_login_rejects_missing_tokens(self):
        del self.login_data['tokenSeguridad']

        with self.assertRaises(CrawlingLoginException):
            self.downloader.login()

    def test_login_rejects_non_json_response(self):
        self.request_post.return_value.json.side_effect = ValueError('HTML')

        with self.assertRaises(CrawlingLoginException):
            self.downloader.login()

    def test_login_rejects_non_object_json(self):
        self.request_post.return_value = self.make_response(data=['OK'])

        with self.assertRaises(CrawlingLoginException):
            self.downloader.login()

    def test_login_transport_error_does_not_expose_secrets(self):
        self.request_post.side_effect = requests.ConnectionError(
            'sensitive-url?jwt=private-token'
        )

        with self.assertRaises(CrawlingLoginException) as error:
            self.downloader.login()

        self.assertNotIn('private-token', str(error.exception))
        self.assertNotIn(self.config.api_key, str(error.exception))

    def test_login_prefers_renewed_jwt_header(self):
        self.request_post.return_value.headers = {'jwt': 'renewed-token'}

        self.downloader.login()

        self.assertEqual(self.downloader.session.headers['jwt'], 'renewed-token')

    def test_post_refreshes_jwt_even_on_http_error(self):
        self.downloader.login()
        self.request_post.return_value = self.make_response(status_code=400)
        self.request_post.return_value.headers = {'jwt': 'renewed-token'}

        self.downloader._post('example', {})

        self.assertEqual(self.downloader.session.headers['jwt'], 'renewed-token')

    def test_post_preserves_jwt_without_renewal(self):
        self.downloader.login()

        self.downloader._post('example', {})

        self.assertEqual(self.downloader.session.headers['jwt'], 'jwt-token')

    def test_post_transport_error_does_not_expose_secrets(self):
        self.request_post.side_effect = requests.Timeout('secret-api-key')

        with self.assertRaises(CrawlingProcessException) as error:
            self.downloader._post('example', {})

        self.assertNotIn('secret-api-key', str(error.exception))

    def test_base_url_accepts_missing_trailing_slash(self):
        self.config.url_portal = self.config.url_portal.rstrip('/')
        downloader = Iberdrola(self.config)
        self.addCleanup(downloader.session.close)

        self.assertEqual(downloader.base_url, self.config.url_portal + '/')

    def test_base_url_defaults_to_production_api(self):
        self.config.url_portal = False
        downloader = Iberdrola(self.config)
        self.addCleanup(downloader.session.close)

        self.assertEqual(
            downloader.base_url, 'https://www.i-de.es/pwelconq/services/arq/'
        )

    def test_start_closes_session(self):
        self.downloader.download_files = mock.Mock()
        self.downloader.session.close = mock.Mock()

        self.downloader.start()

        self.downloader.download_files.assert_called_once_with()
        self.downloader.session.close.assert_called_once_with()

    def test_start_closes_session_on_login_failure(self):
        self.config.api_key = False
        self.downloader.session.close = mock.Mock()

        with self.assertRaises(CrawlingLoginException):
            self.downloader.start()

        self.downloader.session.close.assert_called_once_with()

    def test_download_uses_session_and_documented_endpoint(self):
        self.downloader.login()
        self.request_post.reset_mock()
        self.set_download_response(self.make_zip())

        with self.assertRaises(NoResultsException):
            self.downloader.download_files()

        self.request_post.assert_called_once_with(
            self.config.url_portal + 'DescargarMensajesMasivosAPI',
            json={
                'mensajesFirmados': False,
                'marcados': False,
                'filtros': {
                    'fechaDesde': '01/12/2025 00:00:00',
                    'fechaHasta': '31/12/2025 00:00:00',
                    'tipoInformacion': 'Pendientes Descargar',
                    'proceso': '',
                    'cups': '',
                },
            },
            timeout=300,
            allow_redirects=False,
        )

    def test_download_preserves_process_filter(self):
        self.downloader.process = 'C2'
        self.set_download_response(self.make_zip([('C2.xml', b'<C2/>')]))

        self.downloader.download_files()

        payload = self.request_post.call_args[1]['json']
        self.assertEqual(payload['filtros']['proceso'], 'C2')
        self.assertEqual(payload['filtros']['tipoInformacion'], 'Pendientes Descargar')

    def test_download_all_files_preserves_interval_and_flags(self):
        self.config.pending_files_only = False
        self.downloader.get_intervals.return_value = (
            datetime(2025, 12, 1, 12, 30, 45), datetime(2025, 12, 2, 13, 45, 59),
        )
        self.set_download_response(self.make_zip([('A1.xml', b'<A1/>')]))

        self.downloader.download_files()

        payload = self.request_post.call_args[1]['json']
        self.assertEqual(payload['filtros']['tipoInformacion'], 'Todos')
        self.assertEqual(payload['filtros']['fechaDesde'], '01/12/2025 12:30:45')
        self.assertEqual(payload['filtros']['fechaHasta'], '02/12/2025 13:45:59')
        self.assertFalse(payload['marcados'])
        self.assertFalse(payload['mensajesFirmados'])
        self.assertNotIn('loginUsuario', payload)

    def test_download_maps_documented_http_400_to_no_results(self):
        self.set_download_response(
            b'No se han encontrado mensajes para descargar. Ajuste los filtros.',
            status_code=400, content_type='text/plain',
        )

        self.assert_download_failure(NoResultsException)

    def test_download_distinguishes_message_limit_with_utf8_body(self):
        response = self.set_download_response(
            u'El número de mensajes (14622) supera el límite permitido (1000). '
            u'Ajuste los filtros.'.encode('utf-8'),
            status_code=400, content_type='text/plain',
        )
        # requests may guess Latin-1 for text/plain even when the body is UTF-8.
        response.encoding = 'ISO-8859-1'

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)
        self.assertIn('1000', str(error))

    def test_download_does_not_hide_other_http_400_errors(self):
        self.set_download_response(
            b'Error en el campo fechaDesde: private-detail', status_code=400,
        )

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)
        self.assertIn('HTTP 400', str(error))
        self.assertNotIn('private-detail', str(error))

    def test_download_http_401_is_not_no_results(self):
        self.set_download_response(
            b'No se han encontrado mensajes para descargar.', status_code=401,
        )

        self.assert_download_failure(CrawlingLoginException)

    def test_download_http_403_is_authentication_error(self):
        self.set_download_response(b'', status_code=403)

        self.assert_download_failure(CrawlingLoginException)

    def test_download_http_500_is_not_no_results(self):
        self.set_download_response(
            b'No se han encontrado mensajes para descargar.', status_code=500,
        )

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)
        self.assertIn('HTTP 500', str(error))

    def test_download_rejects_redirect_without_following_it(self):
        response = self.set_download_response(b'', status_code=302)
        response.headers['Location'] = 'https://other.example.test/'

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertIn('HTTP 302', str(error))
        self.assertFalse(self.request_post.call_args[1]['allow_redirects'])
        self.assertEqual(self.request_post.call_count, 1)

    def test_download_rejects_html_with_http_200(self):
        self.set_download_response(
            b'<html>private-detail</html>', content_type='text/html',
        )

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)
        self.assertNotIn('private-detail', str(error))

    def test_download_rejects_json_with_http_200(self):
        self.set_download_response(
            b'{"codigo":"ERROR"}', content_type='application/json',
        )

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)

    def test_download_rejects_empty_http_body(self):
        self.set_download_response(b'')

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)

    def test_download_does_not_accept_pk_prefix_without_valid_zip(self):
        self.set_download_response(b'PK-not-a-zip')

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIsInstance(error, NoResultsException)

    def test_download_rejects_truncated_zip(self):
        content = self.make_zip([('A1.xml', b'<Mensaje/>')])
        self.set_download_response(content[:-10])

        self.assert_download_failure(CrawlingProcessException)

    def test_download_rejects_crc_corruption(self):
        content = self.make_zip([('A1.xml', b'<Mensaje>test</Mensaje>')])
        corrupted = content.replace(b'test', b'fail', 1)
        self.assertNotEqual(content, corrupted)
        self.set_download_response(corrupted)

        self.assert_download_failure(CrawlingProcessException)

    def test_download_rejects_invalid_compressed_data(self):
        filename = 'A1.xml'
        content = self.make_zip(
            [(filename, b'<Mensaje>test</Mensaje>')], compression=zipfile.ZIP_DEFLATED,
        )
        # The fixed local header is 30 bytes and this fixture has no extra fields.
        offset = 30 + len(filename)
        corrupted = content[:offset] + b'\xff' + content[offset + 1:]
        self.set_download_response(corrupted)

        self.assert_download_failure(CrawlingProcessException)

    def test_download_empty_zip_is_no_results(self):
        self.set_download_response(self.make_zip())

        self.assert_download_failure(NoResultsException)

    def test_download_zip_with_only_directories_is_no_results(self):
        self.set_download_response(self.make_zip([('messages/', b'')]))

        self.assert_download_failure(NoResultsException)

    def test_download_saves_valid_binary_without_decoding_or_extracting(self):
        content = self.make_zip(
            [('messages/A1.xml', b'<Mensaje/>')], compression=zipfile.ZIP_DEFLATED,
        )
        self.set_download_response(content, content_type='application/octet-stream')

        self.downloader.download_files()

        with open(self.downloader.target_filename, 'rb') as output:
            self.assertEqual(output.read(), content)
        self.assertEqual(os.listdir(self.output_directory), ['result.zip'])
        self.assertEqual(os.listdir(self.working_directory), ['downloads'])
        self.assertEqual(os.stat(self.downloader.target_filename).st_mode & 0o777, 0o600)

    def test_invalid_download_preserves_existing_target(self):
        with open(self.downloader.target_filename, 'wb') as output:
            output.write(b'existing-content')
        self.set_download_response(b'PK-invalid')

        with self.assertRaises(CrawlingProcessException):
            self.downloader.download_files()

        with open(self.downloader.target_filename, 'rb') as output:
            self.assertEqual(output.read(), b'existing-content')

    @mock.patch('som_crawlers.api_downloaders.iberdrola.os.rename')
    def test_failed_publish_cleans_partial_file_and_preserves_target(self, rename):
        with open(self.downloader.target_filename, 'wb') as output:
            output.write(b'existing-content')
        rename.side_effect = OSError('private-filesystem-detail')
        self.set_download_response(self.make_zip([('A1.xml', b'<Mensaje/>')]))

        with self.assertRaises(CrawlingProcessException) as error:
            self.downloader.download_files()

        self.assertNotIn('private-filesystem-detail', str(error.exception))
        with open(self.downloader.target_filename, 'rb') as output:
            self.assertEqual(output.read(), b'existing-content')
        self.assertEqual(os.listdir(self.working_directory), ['downloads'])

    @mock.patch('som_crawlers.api_downloaders.iberdrola.tempfile.mkstemp')
    def test_failed_staging_does_not_publish_a_file(self, mkstemp):
        mkstemp.side_effect = OSError('private-filesystem-detail')
        self.set_download_response(self.make_zip([('A1.xml', b'<Mensaje/>')]))

        error = self.assert_download_failure(CrawlingProcessException)

        self.assertNotIn('private-filesystem-detail', str(error))
