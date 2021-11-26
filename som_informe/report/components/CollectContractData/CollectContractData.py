
def has_category(pol, category_ids):
    for cat in pol.category_id:
        if cat.id in category_ids:
            return True
    return False

class CollectContractData:
    def __init__(self):
        pass

    def get_data(self,cursor, uid, wiz, context):
        if has_category(wiz.polissa, [11, 27]):
            return {'type': 'CollectContractData'}
        else:
            return {'type': 'Empty'}


