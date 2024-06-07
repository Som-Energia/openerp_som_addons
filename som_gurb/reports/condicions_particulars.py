import os
import pooler
import netsvc
import pypdftk
import tempfile
from report.nterface import report_int


class CondicionsGurbReport(report_int):

    def create(self, cursor, uid, ids, datas, context=None):
        if context is None:
            context = {}

        pool = pooler.get_pool(cursor.dbname)
        gurb_cups_o = pool.get("som.gurb.cups")

        for gurb_cups_id in ids:

            pol_id = gurb_cups_o.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=None)

            report = netsvc.LocalService('report.giscedata.polissa')

            result, result_format = report.create(
                cursor, uid, [pol_id], {}, context=context
            )

    def join_pdfs(self, plain_pdf_files):
        """
        Joins pdf files.
        :param plain_pdf_files: list of pdf files to be joined.
        :type plain_pdf_files: list[str]
        :return: Joined pdf files as plain text.
        :rtype: str
        """
        if len(plain_pdf_files) == 1:
            res = plain_pdf_files[0]
        else:
            pdf_paths = []
            for plain_pdf in plain_pdf_files:
                fd, attachment_path = tempfile.mkstemp('-join.pdf', 'report-')
                os.write(fd, plain_pdf)
                os.close(fd)

                pdf_paths.append(attachment_path)

            pdf_path = pypdftk.concat(files=pdf_paths)

            for tmp_file in pdf_paths:
                os.remove(tmp_file)

            with open(pdf_path, 'r') as full_pdf:
                res = full_pdf.read()

            os.remove(pdf_path)

        return res


CondicionsGurbReport()
