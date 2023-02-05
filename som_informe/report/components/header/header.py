from ..component_utils import dateformat

class header:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        pol_data = wiz.polissa
        baixa = False
        if pol_data.data_baixa:
            baixa = dateformat(pol_data.data_baixa)

        # bloc per traure una línea amb la tarifa i potencies per periode
        tarifa_code = pol_data.tarifa_codi
        list_potencies = []
        str_tarifa_potencies_periode = ""
        str_potencies_periode = ""        
        for periode_potencia_id in pol_data.potencies_periode:
            period_name = periode_potencia_id.periode_id.name
            potencia = periode_potencia_id.potencia
            str_potencies_periode += "{} - "



        return {
            'type': 'header',
            'data_alta': dateformat(pol_data.data_alta, False),
            'data_baixa': baixa,
            'contract_number': pol_data.name,
            'titular_name': pol_data.titular.name,
            'titular_nif': pol_data.titular_nif[2:11],
            'distribuidora': pol_data.distribuidora.name,
            'distribuidora_contract_number': pol_data.ref_dist,
            'cups': pol_data.cups.name,
            'cups_address': pol_data.cups_direccio,
        }
