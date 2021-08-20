from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC1 import ProcesC1

class C105(ProcesC1.ProcesC1):
    def __init__(self):
        ProcesC1.ProcesC1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC1.ProcesC1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C105'
        result['tipus_contracte'] =  get_description(step.tipus_contracte, "TABLA_9")
        result['tipus_autoconsum'] =  get_description(step.tipus_autoconsum, "TABLA_113")
        result['codi_contracte'] = step.contracte_atr
        result ['potencies'] = []
        for pot in step.pot_ids:
            result['potencies'].append({
                    'name' : pot.name,
                    'potencia' : pot.potencia
                })
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['tensio'] = get_description(step.tensio_suministre, "TABLA_64")
        result['data_activacio'] = dateformat(step.data_activacio)

        return result