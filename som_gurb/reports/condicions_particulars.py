import os
import uuid
import pooler
import netsvc
import pypdftk
import tempfile
from base64 import b64decode
from report.interface import report_int


class ConditionsGurbReport(report_int):

    def create(self, cursor, uid, ids, datas, context=None):
        if context is None:
            context = {}

        pool = pooler.get_pool(cursor.dbname)
        gurb_cups_o = pool.get("som.gurb.cups")

        for gurb_cups_id in ids:
            pol_id = gurb_cups_o.get_polissa_gurb_cups(
                cursor, uid, gurb_cups_id, context=context
            )

            report = netsvc.LocalService('report.giscedata.polissa')

            res = []
            contract_pdf, doc_type = report.create(cursor, uid, [pol_id], {}, context=context)
            if doc_type == 'pdf':
                condicions_generals_pdf = gurb_cups_o.browse(
                    cursor, uid, gurb_cups_id).general_conditions_id.attachment_id.datas
                pdfs = [
                    contract_pdf, b64decode(condicions_generals_pdf)
                ]
                tmp_dir = tempfile.gettempdir()
                for pdf in pdfs:
                    pdf_file_name = '{}.pdf'.format(uuid.uuid4())
                    pdf_file_path = os.path.join(tmp_dir, pdf_file_name.replace(' ', ''))
                    with open(pdf_file_path, 'w') as pdf_file:
                        pdf_file.write(pdf)
                    res.append(pdf_file_path)

                result = self.join_pdfs(res)

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


ConditionsGurbReport('report.som.gurb.conditions')
