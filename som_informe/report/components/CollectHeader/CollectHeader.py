class CollectHeader:
    def __init__(self):
        pass

    def get_data(self, w, cursor, uid, wiz, context):
        pol = wiz.polissa
        return {
            'type': 'CollectHeader',
            'date': '2030-01-01',
            'contract_number': pol.name,
            'unpaid_invoices': pol.unpaid_invoices,
            'unpaid_amount': pol.debt_amount,
        }
