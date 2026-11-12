# -*- coding: utf-8 -*-
from __future__ import absolute_import

import csv
import io
import sys


CSV_COLUMNS = (
    'name', 'description', 'priority', 'active', 'report_name',
    'report_model', 'interpreter', 'value',
)
PY2 = sys.version_info[0] == 2


def _read_header(reader):
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError(u'El fitxer CSV és buit.')
    except csv.Error:
        raise ValueError(u'La capçalera del CSV té un format incorrecte.')
    if PY2:
        header = [cell.decode('utf-8') for cell in header]
    header = [cell.strip().lower() for cell in header]
    if 'value' not in header:
        raise ValueError(u"El CSV ha de contenir una columna 'value'.")
    if len(header) != len(set(header)):
        raise ValueError(u'El CSV conté noms de columna repetits.')
    unknown = set(header) - set(CSV_COLUMNS)
    if unknown:
        raise ValueError(u'Columnes desconegudes al CSV: {}.'.format(u', '.join(sorted(unknown))))
    return header


def read_test_csv(content):
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError(u"El fitxer CSV ha d'estar codificat en UTF-8.")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ','
    if PY2:
        delimiter = delimiter.encode('ascii')
    stream = io.BytesIO(text.encode('utf-8')) if PY2 else io.StringIO(text)
    reader = csv.reader(stream, delimiter=delimiter, strict=True)
    header = _read_header(reader)

    rows = []
    try:
        for cells in reader:
            if PY2:
                cells = [cell.decode('utf-8') for cell in cells]
            if not any(cell.strip() for cell in cells):
                continue
            if len(cells) != len(header):
                raise ValueError(u'Línia {} del CSV: nombre de columnes incorrecte.'.format(
                    reader.line_num
                ))
            rows.append((reader.line_num, dict(zip(header, cells))))
    except csv.Error:
        raise ValueError(u'Línia {} del CSV: format incorrecte; reviseu les cometes.'.format(
            reader.line_num
        ))
    if not rows:
        raise ValueError(u'El CSV no conté cap test.')
    return rows


def write_test_csv(rows):
    stream = io.BytesIO() if PY2 else io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        cells = [row.get(column, '') for column in CSV_COLUMNS]
        if PY2:
            cells = [cell.encode('utf-8') if isinstance(cell, type(u'')) else cell
                     for cell in cells]
        writer.writerow(cells)
    content = stream.getvalue()
    if not PY2:
        content = content.encode('utf-8')
    return b'\xef\xbb\xbf' + content
