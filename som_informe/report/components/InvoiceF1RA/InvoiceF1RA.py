from datetime import date

class InvoiceF1RA:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, invoice, context):
        return {
            'type': 'InvoiceF1RA',
            'date': date.today().strftime("%d/%m/%Y"),
        }
