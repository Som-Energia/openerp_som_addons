from ..component_utils import dateformat

class CollectExpectedCutOffDate:
    def __init__(self):
        pass

    def get_data(self,cursor, uid, wiz, context):
        return {
            'type': 'CollectExpectedCutOffDate',
            'expected_cut_off_date' : 'TODO find the date',
            'distri_name' : wiz.polissa.distribuidora.name,
        }




