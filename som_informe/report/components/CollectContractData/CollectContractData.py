from ..component_utils import has_category


class CollectContractData:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        if has_category(wiz.polissa, [11, 27]):
            return {"type": "CollectContractData"}
        else:
            return {"type": "Empty"}
