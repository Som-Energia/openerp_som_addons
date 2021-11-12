from ..component_utils import dateformat

class header:
    def __init__(self):
        pass

    def get_data(self, w, cursor, uid, wiz, context):
        pol_data = wiz.polissa
        return {
            'type': 'header',
            'data_alta': dateformat(pol_data.data_alta, False),
            'contract_number': pol_data.name,
            'titular_name': pol_data.titular.name,
            'titular_nif': pol_data.titular_nif[2:11],
            'distribuidora': pol_data.distribuidora.name,
            'distribuidora_contract_number': pol_data.ref_dist,
            'cups': pol_data.cups.name,
            'cups_address': pol_data.cups_direccio,
        }
