from datetime import date

class InvoiceF1C:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):
        return {
            'type': 'InvoiceF1C',
            'date': date.today().strftime("%d/%m/%Y"),
        }
