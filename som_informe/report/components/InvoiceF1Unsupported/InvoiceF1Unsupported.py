from datetime import date

class InvoiceF1Unsupported:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):
        return {
            'type': 'InvoiceF1Unsupported',
            'date': date.today().strftime("%d/%m/%Y"),
        }

