# -*- coding: utf-8 -*-
import pooler
import base64


class InvoicePdfStorer():

    def __init__(self, cursor, uid, context):
        self.cursor = cursor
        self.uid = uid
        self.pool = pooler.get_pool(cursor.dbname)
        self.context = {} if context is None else context
        self.result = []
        self.fact_obj = self.pool.get("giscedata.facturacio.factura")
        self.att_obj = self.pool.get("ir.attachment")

    def search_stored_and_append(self, fact_id):
        fact_number = self.get_storable_fact_number(fact_id)
        if not fact_number:
            return False

        found = False
        att_id = None

        # ToDo: search it in the mails
        if not found:
            # ToDo: search it in the attachements
            if not found:
                return False

        result = self.read_file(att_id)
        self.result.append(result)
        return True

    def append_and_store(self, fact_id, result):
        self.result.append(result)
        fact_number = self.get_storable_fact_number(fact_id)
        if fact_number:
            file_name = self.get_store_filename(fact_number)
            if not self.exists_file(file_name, fact_id):
                self.store_file(result[0], file_name, fact_id)

    def retrieve(self):
        if len(self.result) == 1:
            return self.result[0]
        # ToDo: pdf concatenation if n results

    def get_storable_fact_number(self, fact_id):
        if self.context.get("regenerate_pdf", False):
            return False

        fact_number = self.fact_obj.read(
            self.cursor,
            self.uid,
            fact_id,
            ['number'],
            context=self.context
        )['number']
        if not fact_number:
            return False

        # ToDo: add more contitions
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
