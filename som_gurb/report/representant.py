import os
import uuid
import pooler
import pypdftk
import tempfile
from base64 import b64decode
from report.interface import report_int


class RepresentantGurbReport(report_int):

    def create(self, cursor, uid, ids, datas, context=None):
        if context is None:
            context = {}

        pool = pooler.get_pool(cursor.dbname)
        gurb_cups_o = pool.get("som.gurb.cups")
        ir_attachment_o = pool.get("ir.attachment")

        for gurb_id in ids:
            reports = []

            search_params = [
                ("gurb_id", "=", gurb_id),
                ("active", "=", True)
            ]

            gurb_cups_ids = gurb_cups_o.search(cursor, uid, search_params, context=context)

            for gurb_cups_id in gurb_cups_ids:
                search_params = [
                    ("res_model", "=", "som.gurb.cups"),
                    ("res_id", "=", gurb_cups_id),
                    ("name", "like", "%representant%")
                ]

                attach_ids = ir_attachment_o.search(cursor, uid, search_params, context=context)

                pdfs = []

                for attach_id in attach_ids:
                    report_data = ir_attachment_o.read(cursor, uid, attach_id, ['datas'])['datas']
                    pdfs.append(b64decode(report_data))

                tmp_dir = tempfile.gettempdir()
                for pdf in pdfs:
                    pdf_file_name = '{}.pdf'.format(uuid.uuid4())
                    pdf_file_path = os.path.join(tmp_dir, pdf_file_name.replace(' ', ''))
                    with open(pdf_file_path, 'w') as pdf_file:
                        pdf_file.write(pdf)
                    reports.append(pdf_file_path)

            result = self.join_pdfs(reports)

            return result, 'pdf'

    def join_pdfs(self, pdf_paths):
        """
        Joins pdf files.
        :param pdf_files: list of pdf path files to be joined.
        :type pdf_files: list[str]
        :return: Joined pdf files as plain text.
        :rtype: str
        """
        if len(pdf_paths) == 1:
            res = pdf_paths[0]
        else:
            pdf_path = pypdftk.concat(files=pdf_paths)

            for tmp_file in pdf_paths:
                os.remove(tmp_file)

            with open(pdf_path, 'r') as full_pdf:
                res = full_pdf.read()

            os.remove(pdf_path)

        return res


RepresentantGurbReport('report.report_som_gurb_representant')
