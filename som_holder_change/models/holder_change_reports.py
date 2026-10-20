# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
import os
from uuid import uuid4

import netsvc
import pypdftk
from report_puppeteer.report_puppeteer import PuppeteerParser
from service.security import Sudo


CARD_PLACEHOLDER_CONTEXT = "holder_change_card_placeholder"
REPORTS = (
    ("report.giscedata.polissa.contract.summary", "report.backend.contract.summary"),
    ("report.giscedata.polissa", "report.backend.condicions.particulars"),
)


def prepare_snapshot(cursor, uid, pool, polissa_id, context=None):
    """Freeze translated HTML while the simulated contract still exists."""
    placeholder = "HOLDER_CHANGE_CARD_{}".format(uuid4().hex)
    report_context = dict(context or {})
    report_context[CARD_PLACEHOLDER_CONTEXT] = placeholder
    documents = []
    group_id = pool.get("res.users").read(cursor, uid, uid, ["groups_id"])["groups_id"][0]
    for report_name, backend_name in REPORTS:
        parser = netsvc.LocalService(report_name)._service
        with Sudo(uid=uid, gid=group_id):
            html_context = dict(report_context, report_name=report_name)
            parser._clean_backend_context(html_context)
            report_values = parser.get_report_v(cursor, uid, context=html_context)
            parser.id = report_values["id"]
            html_context.update(report_values["context"])
            # Parse HTML directly: report.create() would also generate a PDF.
            # Keep PDF mode here so template errors are raised, not rendered
            # as HTML debug pages that could otherwise be saved as documents.
            report_values["report_type"] = "pdf"
            html = parser.create_html(
                cursor, uid, [polissa_id], {}, report_values, context=html_context
            )
            appended_pdfs = pool.get(backend_name).get_pdfs_to_append(
                cursor, uid, polissa_id, context=dict(context or {}, report_name=report_name)
            )
        if isinstance(html, bytes):
            html = html.decode("utf-8")
        if placeholder not in html:
            raise ValueError("The card report could not be prepared: {}".format(report_name))
        documents.append({
            "html": html,
            "appended_pdfs": [base64.b64encode(pdf).decode("ascii") for pdf in appended_pdfs],
        })
    return {"version": 1, "card_placeholder": placeholder, "documents": documents}


def render_snapshot(snapshot, masked_number, context=None):
    """Render frozen documents without reading the original or simulated contract."""
    if not snapshot or snapshot.get("version") != 1:
        raise ValueError("The prepared card reports are missing or unsupported.")
    last4 = "".join(char for char in masked_number if char.isdigit())[-4:]
    if len(last4) != 4:
        raise ValueError("The masked card number must contain its last four digits.")
    placeholder = snapshot["card_placeholder"]
    documents = snapshot["documents"]
    if len(documents) != len(REPORTS) or not placeholder:
        raise ValueError("The prepared card reports are incomplete.")
    paths = []
    merged_path = None
    try:
        for document in documents:
            if placeholder not in document["html"]:
                raise ValueError("The prepared card report has no card placeholder.")
            html = document["html"].replace(placeholder, last4)
            paths.append(PuppeteerParser.render(html.encode("utf-8"), params={}, context=context))
            for pdf in document["appended_pdfs"]:
                paths.append(PuppeteerParser.write_temporal_file(base64.b64decode(pdf), "pdf"))
        merged_path = pypdftk.concat(files=paths)
        with open(merged_path, "rb") as pdf_file:
            return {"contract_pdf": base64.b64encode(pdf_file.read()), "mandate_pdf": False}
    finally:
        for path in set(paths + ([merged_path] if merged_path else [])):
            if os.path.exists(path):
                os.remove(path)
