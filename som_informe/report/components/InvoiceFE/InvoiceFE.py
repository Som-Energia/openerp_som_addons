from datetime import date

class InvoiceFE:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, invoice, context):
        return {
            'type': 'InvoiceFE',
            'date': date.today().strftime("%d/%m/%Y"),
        }

