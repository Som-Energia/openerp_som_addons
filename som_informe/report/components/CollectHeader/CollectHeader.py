from ..component_utils import is_enterprise


class CollectHeader:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        pol = wiz.polissa
        return {
            "type": "CollectHeader",
            "contract_number": pol.name,
            "unpaid_invoices": pol.unpaid_invoices,
            "unpaid_amount": pol.debt_amount,
            "is_enterprise": is_enterprise(pol),
        }
