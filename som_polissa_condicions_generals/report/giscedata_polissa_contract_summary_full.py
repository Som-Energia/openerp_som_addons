# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import tempfile

import netsvc
import pypdftk
from report.interface import report_int


class ContractSummaryFullReport(report_int):

    def create(self, cursor, uid, ids, datas, context=None):
        summary_service = netsvc.LocalService(
            'report.giscedata.polissa.contract.summary'
        )
        contract_service = netsvc.LocalService('report.giscedata.polissa')

        summary_pdf, _doc_format = summary_service.create(
            cursor, uid, ids, datas, context
        )
        contract_pdf, _doc_format = contract_service.create(
            cursor, uid, ids, datas, context
        )

        return self.join_pdfs([summary_pdf, contract_pdf]), 'pdf'

    def join_pdfs(self, pdfs):
        pdf_paths = []
        merged_path = None
        try:
            for pdf in pdfs:
                file_descriptor, pdf_path = tempfile.mkstemp(suffix='.pdf')
                pdf_paths.append(pdf_path)
                pdf_file = None
                try:
                    pdf_file = os.fdopen(file_descriptor, 'wb')
                    pdf_file.write(pdf)
                finally:
                    if pdf_file:
                        pdf_file.close()
                    else:
                        os.close(file_descriptor)

            merged_path = pypdftk.concat(files=pdf_paths)
            with open(merged_path, 'rb') as merged_file:
                return merged_file.read()
        finally:
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            if merged_path and os.path.exists(merged_path):
                os.remove(merged_path)


ContractSummaryFullReport('report.giscedata.polissa.contract.summary.full')
