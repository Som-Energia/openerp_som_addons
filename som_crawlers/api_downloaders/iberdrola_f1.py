# -*- coding: utf-8 -*-
from __future__ import absolute_import

import io
import logging
import re
import time
from time import sleep
import zipfile

from six import string_types

from som_crawlers.api_downloaders.iberdrola import Iberdrola
from som_crawlers.models.exceptions import CrawlingProcessException, NoResultsException


logger = logging.getLogger(__name__)
# Python 2 has no monotonic clock in the standard library. The polling count
# also bounds retries if the fallback wall clock moves backwards.
_clock = getattr(time, 'monotonic', time.time)


def instance(_config, **_kwargs):
    return Iberdrola_F1(_config)


class Iberdrola_F1(Iberdrola):
    name = 'iberdrola_f1'
    process = 'F1'
    ticket_poll_interval = 60
    ticket_timeout = 1800
    ticket_max_polls = 31

    def __init__(self, config):
        super(Iberdrola_F1, self).__init__(config)
        self.ticket_code = None

    def download_files(self):
        if self.ticket_code is None:
            self.ticket_code = self._create_ticket()
            logger.info('i-DE %s: created ticket %s', self.name, self.ticket_code)
        else:
            logger.info('i-DE %s: resuming ticket %s', self.name, self.ticket_code)
        ticket_code = self.ticket_code

        try:
            self._wait_for_ticket(ticket_code)
            response = self._post(
                'ConsultaDescargaAPI', {'codDescarga': ticket_code},
                timeout=self.download_timeout,
            )
            self._check_download_response(response)
            self._validate_zip(response.content)
            filtered = self._filter_f1_zip(response.content)
            self._validate_zip(filtered)
            self._save_zip(filtered)
        except NoResultsException:
            self.ticket_code = None
            raise

        # Keep the ticket on failures so a retry on this instance can resume it.
        # Across ERP executions the operator can recover its code from the log.
        self.ticket_code = None
        logger.info('i-DE %s: ticket %s downloaded and filtered', self.name, ticket_code)

    def _ticket_json(self, response):
        self._check_download_response(response)
        try:
            data = response.json()
        except ValueError:
            data = None
        if not isinstance(data, dict):
            raise CrawlingProcessException(
                "Resposta JSON invàlida del servei de tickets d'i-DE"
            )
        return data

    def _create_ticket(self):
        start, end = self.get_intervals()
        payload = {
            'agenteSolicitante': self.cod_portal,
            'fechaDesde': start.strftime('%Y-%m-%d'),
            'fechaHasta': end.strftime('%Y-%m-%d'),
            'horaDesde': start.strftime('%H:%M:%S'),
            'horaHasta': end.strftime('%H:%M:%S'),
            # i-DE confirmed this field has no effect. Filter the ZIP locally.
            'filtro': '',
            'firmado': False,
            'marcarDescargados': False,
            'tipoInformacion': (
                'Pendientes Descargar' if self.config.pending_files_only else 'Todos'
            ),
        }
        response = self._post(
            'API/gmagente/DescargaAbsoluta', payload,
            timeout=self.download_timeout,
        )
        data = self._ticket_json(response)
        # Real response observed on the server: {"codigoDescarga": "28282"}.
        ticket_code = data.get('codigoDescarga')
        if (
            not isinstance(ticket_code, string_types)
            or not re.match(r'\A[0-9]+\Z', ticket_code)
            or not ticket_code.strip('0')
        ):
            raise CrawlingProcessException(
                "La resposta d'i-DE no conté un codigoDescarga vàlid"
            )
        return str(ticket_code)

    def _wait_for_ticket(self, ticket_code):
        deadline = _clock() + self.ticket_timeout
        for attempt in range(self.ticket_max_polls):
            remaining = deadline - _clock()
            if remaining <= 0:
                break
            response = self._post(
                'API/gmagente/ConsultarEstadoTicket',
                {'codDescarga': ticket_code},
                timeout=min(self.request_timeout, remaining),
            )
            data = self._ticket_json(response)
            if _clock() >= deadline:
                break
            state = data.get('estado')
            if state == 'F':
                return
            if state != 'P':
                # Unknown states are errors, not empty downloads. Do not log
                # arbitrary messages or JSON values from the remote server.
                raise CrawlingProcessException(
                    "Estat inesperat del ticket {} d'i-DE".format(ticket_code)
                )
            remaining = deadline - _clock()
            if remaining <= 0 or attempt + 1 >= self.ticket_max_polls:
                break
            sleep(min(self.ticket_poll_interval, remaining))

        raise CrawlingProcessException(
            "S'ha esgotat el temps d'espera del ticket {} d'i-DE. "
            "Podeu consultar-lo i descarregar-lo manualment quan estigui preparat.".format(
                ticket_code
            )
        )

    def _filter_f1_zip(self, content):
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(content), 'r') as source:
            selected = []
            file_count = 0
            for item in source.infolist():
                # Match the file name, not a parent directory named F1.
                filename = item.filename.replace('\\', '/').rsplit('/', 1)[-1]
                if not filename:
                    continue
                file_count += 1
                if filename.lower().endswith('.xml') and 'F1' in filename.upper():
                    selected.append(item)
            if not selected:
                raise NoResultsException("El ZIP no conté fitxers XML F1")
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as target:
                for item in selected:
                    target.writestr(item.filename, source.read(item))

        logger.info(
            'i-DE %s: selected %s XML files from %s files in the absolute download',
            self.name, len(selected), file_count,
        )
        return output.getvalue()
