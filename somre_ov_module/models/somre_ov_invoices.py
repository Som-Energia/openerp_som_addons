# -*- coding: utf-8 -*-
from osv import osv
import netsvc
import base64
import zipfile
import re

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from decorators import www_entry_point
from exceptions import NoSuchUser, NoSuchInvoice, UnauthorizedAccess


class SomreOvInvoices(osv.osv_memory):

    _name = 'somre.ov.invoices'

    CONCEPT_TYPE = {
        '01': 'market',
        '02': 'specific_retribution',
        '03': 'services',
    }

    COMPLEMENTARY_LIQUIDATION = 'COMPLEMENTARY'
    OLDEST_INVOICE_EMISSION_DATE = '2024-05-16'

    @www_entry_point(
        expected_exceptions=(
            NoSuchUser,
        )
    )
    def get_invoices(
            self,
            cursor,
            uid,
            vat,
            oldest_date=OLDEST_INVOICE_EMISSION_DATE,
            context=None,
    ):
        if context is None:
            context = {}

        users_obj = self.pool.get('somre.ov.users')
        ov_user = users_obj.get_customer(cursor, uid, vat)
        invoice_obj = self.pool.get('giscere.facturacio.factura')

        search_params = [
            ('partner_id', '=', ov_user.partner_id.id),
            ('state', 'in', ['open', 'paid']),
        ]
        if oldest_date:
            search_params.append(
                ('date_invoice', '>=', oldest_date),
            )

        invoice_ids = invoice_obj.search(cursor, uid, search_params)

        invoices = invoice_obj.browse(cursor, uid, invoice_ids)
        return [
            dict(
                contract_number=invoice.polissa_id.name,
                invoice_number=invoice.number,
                concept=self.CONCEPT_TYPE[invoice.tipo_factura],
                emission_date=invoice.date_invoice,
                first_period_date=invoice.data_inici,
                last_period_date=invoice.data_final,
                amount=invoice.amount_total,
                payment_status=invoice.state,
                liquidation=self.get_liquidation_description(
                    cursor, uid, invoice.tipo_factura, invoice.id),
            )
            for invoice in invoices
        ]

    def validate_invoices(self, cursor, uid, invoice_obj, vat, invoice_numbers):
        invoice_numbers = self.ensure_list(invoice_numbers)
        users_obj = self.pool.get('somre.ov.users')
        ov_user = users_obj.get_customer(cursor, uid, vat)

        search_params = [
            ('number', 'in', invoice_numbers),
        ]

        invoice_ids = invoice_obj.search(cursor, uid, search_params)

        for invoice_id in invoice_ids:
            invoice = invoice_obj.browse(cursor, uid, invoice_id)

            if invoice.partner_id.id != ov_user.partner_id.id:
                raise UnauthorizedAccess(
                    username=vat,
                    resource_type='Invoice',
                    resource_name=invoice.number,
                )
        return invoice_ids

    def ensure_list(self, value):
        if not isinstance(value, (tuple, list)):
            return [value]
        return value

    def do_invoice_pdf(
            self,
            cursor,
            uid,
            report_factura_obj,
            invoice_obj,
            invoice_id,
            context=None
    ):
        invoice_ids = self.ensure_list(invoice_id)
        result, result_format = report_factura_obj.create(
            cursor, uid, invoice_ids, {}, context=context)

        invoice = invoice_obj.browse(cursor, uid, invoice_ids)[0]

        filename = (
            '{invoice_code}_{cil}.pdf'
        ).format(
            invoice_code=invoice.number,
            cil=invoice.cil_id.name,
        )

        return result, result_format, filename

    @www_entry_point(
        expected_exceptions=(
            NoSuchUser,
            NoSuchInvoice,
            UnauthorizedAccess,
        )
    )
    def download_invoice_pdf(self, cursor, uid, vat, invoice_number, context=None):
        context = context if context is not None else {}
        invoice_obj = self.pool.get('giscere.facturacio.factura')

        invoice_ids = self.validate_invoices(
            cursor, uid, invoice_obj, vat, invoice_number)
        if not invoice_ids:
            raise NoSuchInvoice(invoice_number)

        report_factura_obj = netsvc.LocalService('report.giscere.factura')

        result, result_format, filename = self.do_invoice_pdf(
            cursor, uid, report_factura_obj, invoice_obj, invoice_ids, context)

        return dict(
            content=base64.b64encode(result),
            filename=filename,
            content_type='application/{}'.format(result_format),
        )

    @www_entry_point(
        expected_exceptions=(
            NoSuchUser,
            UnauthorizedAccess,
        )
    )
    def download_invoices_zip(self, cursor, uid, vat, invoice_numbers, context=None):
        context = context if context is not None else {}
        invoice_obj = self.pool.get('giscere.facturacio.factura')

        invoice_ids = self.validate_invoices(
            cursor, uid, invoice_obj, vat, invoice_numbers)

        report_factura_obj = netsvc.LocalService('report.giscere.factura')

        zipfile_io = StringIO.StringIO()
        zipfile_ = zipfile.ZipFile(
            zipfile_io, 'w', compression=zipfile.ZIP_DEFLATED
        )

        for invoice_id in invoice_ids:
            result, result_format, filename = self.do_invoice_pdf(
                cursor, uid, report_factura_obj, invoice_obj, [invoice_id], context)
            zipfile_.writestr(filename, result)

        zipfile_.close()

        return dict(
            content=base64.b64encode(zipfile_io.getvalue()),
            filename='{}_invoices_from_{}.zip'.format(vat, invoice_numbers[0]),
            content_type='application/{}'.format(result_format),
        )

    def get_extra_line(self, cursor, uid, tipo_factura, invoice_id):
        specific_retribution_type_value = '02'
        if tipo_factura != specific_retribution_type_value:
            return None

        extra_obj = self.pool.get('giscere.facturacio.extra')
        params = [
            ('factura_ids', '=', invoice_id)
        ]
        extra_line_ids = extra_obj.search(cursor, uid, params)

        if extra_line_ids:
            return extra_obj.browse(cursor, uid, extra_line_ids[0])
        return None

    def extract_retribution_liquidation_description(self, extra_line):
        extract_month_pattern = r'(\d{4})/(\d{2})'
        match = re.search(extract_month_pattern, extra_line.name)
        if match:
            return match.group(2)

    def get_liquidation_description(self, cursor, uid, tipo_factura, invoice_id):
        extra_line = self.get_extra_line(cursor, uid, tipo_factura, invoice_id)
        if extra_line:
            if extra_line.type_extra == 'complementary':
                return self.COMPLEMENTARY_LIQUIDATION
            if extra_line.type_extra == 'retribution':
                return self.extract_retribution_liquidation_description(extra_line)
        return None


SomreOvInvoices()
