from ..component_utils import dateformat


class InvoiceF1Unsupported:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):

        result = {}

        # camps obligats per estructura
        result["type"] = "InvoiceF1Unsupported"
        result["date"] = invoice.date_invoice
        result["date_final"] = invoice.data_final

        result["invoice_type"] = invoice.rectificative_type
        result["invoice_date"] = (
            dateformat(invoice.origin_date_invoice)
            if invoice.origin_date_invoice
            else dateformat(invoice.date_invoice)
        )
        result["invoice_number"] = invoice.origin
        result["invoice_id"] = invoice.id
        result["date_from"] = dateformat(invoice.data_inici)
        result["date_to"] = dateformat(invoice.data_final)

        return result
