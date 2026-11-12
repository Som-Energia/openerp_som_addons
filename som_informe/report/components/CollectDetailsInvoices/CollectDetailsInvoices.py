from ..component_utils import dateformat

ESTAT_PENDENT_INPAGAT_MIN = 33


class CollectDetailsInvoices:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        fact_obj = wiz.pool.get("giscedata.facturacio.factura")
        search_parameters = [
            ("polissa_id", "=", wiz.polissa.id),
            ("type", "in", ("out_invoice", "out_refund")),
        ]
        if wiz.date_from:
            search_parameters.append(("data_inici", ">=", wiz.date_from))
        if wiz.date_to:
            search_parameters.append(("data_final", "<=", wiz.date_to))
        if wiz.mostrar_cobraments_factures == "debt":
            search_parameters.append(("residual", ">", 0))
            search_parameters.append(("pending_state", ">", ESTAT_PENDENT_INPAGAT_MIN))

        facts = fact_obj.search(cursor, uid, search_parameters)

        invoices_data = []
        for fact in facts:
            invoice = fact_obj.browse(cursor, uid, fact)
            data = {
                "invoice_number": invoice.number,
                "data_inici": dateformat(invoice.data_inici),
                "data_final": dateformat(invoice.data_final),
                "invoice_date": dateformat(invoice.date_invoice),
                "due_date": dateformat(invoice.date_due),
                "devolucio_date": dateformat(invoice.devolucio_id.date),
                "amount_total": invoice.amount_total,
                "pending_amount": invoice.residual,
            }
            invoices_data.append(data)
        return {"type": "CollectDetailsInvoices", "invoices_data": invoices_data}
