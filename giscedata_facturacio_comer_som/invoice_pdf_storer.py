# -*- coding: utf-8 -*-
import os
import uuid
import pooler
import base64
import pypdftk
import tempfile


class InvoicePdfStorer():

    def __init__(self, cursor, uid, context):
        self.cursor = cursor
        self.uid = uid
        self.pool = pooler.get_pool(cursor.dbname)
        self.context = {} if context is None else context
        self.result = []
        self.fact_obj = self.pool.get("giscedata.facturacio.factura")
        self.att_obj = self.pool.get("ir.attachment")
        self.mailb_obj = self.pool.get("poweremail.mailbox")
        self.conf_obj = self.pool.get("res.config")
        flags = self.conf_obj.get(self.cursor, self.uid, "factura_pdf_cache_flags", None)
        self.flags = eval(flags) if flags else []

    def is_enabled(self):
        if 'Enabled' not in self.flags:
            return False

        if self.context.get("do_not_use_stored_pdf", False):
            return False

        return True

    def search_stored_and_append(self, fact_id):
        fact_number = self.get_storable_fact_number(fact_id)
        if not fact_number:
            return False

        file_name = self.get_store_filename(fact_number)
        att_ids = self.exists_file(file_name, fact_id)
        if not att_ids:
            att_ids = self.exists_mailbox_file(fact_id)
            if not att_ids:
                return False

        result = self.read_file(att_ids[0])
        self.result.append(result)
        return True

    def append_and_store(self, fact_id, result):
        self.result.append(result)
        if self.context.get("save_pdf_in_invoice_attachments", False):
            fact_number = self.get_storable_fact_number(fact_id)
            if fact_number:
                file_name = self.get_store_filename(fact_number)
                if not self.exists_file(file_name, fact_id):
                    self.store_file(result[0], file_name, fact_id)

    def retrieve(self):
        if len(self.result) == 1:
            return self.result[0]

        pdf_paths = []
        tmp_dir = tempfile.gettempdir()
        for print_result in self.result:
            pdf_file_name = '{}.pdf'.format(uuid.uuid4())
            pdf_file_path = os.path.join(tmp_dir, pdf_file_name.replace(' ', ''))
            with open(pdf_file_path, 'w') as pdf_file:
                pdf_file.write(print_result[0])
            pdf_paths.append(pdf_file_path)

        pdf_file_name = '{}.pdf'.format(uuid.uuid4())
        pdf_path = os.path.join(tmp_dir, pdf_file_name.replace(' ', ''))

        pypdftk.concat(files=pdf_paths, out_file=pdf_path)

        with open(pdf_path, 'r') as full_pdf:
            merged_pdf = full_pdf.read()

        for tmp_file in pdf_paths:
            os.remove(tmp_file)
        os.remove(pdf_path)

        return [merged_pdf, u'pdf']

    def get_storable_fact_number(self, fact_id):
        fact_data = self.fact_obj.read(
            self.cursor,
            self.uid,
            fact_id,
            ['number', 'state'],
            context=self.context
        )
        fact_state = fact_data['state']
        if fact_state not in ['open', 'paid']:
            return False

        fact_number = fact_data['number']
        if not fact_number:
            return False

        return fact_number

    def get_store_filename(self, fact_number):
        return 'STORED_{}.pdf'.format(fact_number)

    def exists_file(self, file_name, fact_id):
        att_ids = self.att_obj.search(
            self.cursor,
            self.uid,
            [
                ('name', '=', file_name),
                ('res_model', '=', 'giscedata.facturacio.factura'),
                ('res_id', '=', fact_id),
            ],
            context=self.context
        )
        return att_ids

    def store_file(self, content, file_name, fact_id):
        if 'Dont_store' in self.flags:
            return []
        b64_content = base64.b64encode(content)
        attachment = {
            "name": file_name,
            "datas": b64_content,
            "datas_fname": file_name,
            "res_model": "giscedata.facturacio.factura",
            "res_id": fact_id,
        }
        with pooler.get_db(self.cursor.dbname).cursor() as w_cursor:
            attachment_id = self.att_obj.create(
                w_cursor, self.uid, attachment, context=self.context
            )
        return attachment_id

    def read_file(self, att_id):
        b64_content = self.att_obj.read(
            self.cursor,
            self.uid,
            att_id,
            ["datas"],
            context=self.context
        )["datas"]
        content = base64.b64decode(b64_content)
        return [content, u'pdf']

    def exists_mailbox_file(self, fact_id):
        mail = self.fact_obj.read(
            self.cursor,
            self.uid,
            fact_id,
            ['enviat_mail_id'],
            context=self.context,
        )['enviat_mail_id']

        if not mail:
            return []

        result = self.mailb_obj.read(
            self.cursor,
            self.uid,
            mail[0],
            ['pem_attachments_ids'],
            context=self.context,
        )['pem_attachments_ids']

        if 'No_mongo' in self.flags:
            return []
        return result
