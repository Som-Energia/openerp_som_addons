from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3

class A305(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A305'
        result['tipus_contracte'] =  get_description(step.tipus_contracte, "TABLA_9")
        result['codi_contracte'] = step.contracte_atr
        result ['potencies'] = []
        for pot in step.pot_ids:
            if pot.potencia != 0:
                result['potencies'].append({
                        'name' : pot.name,
                        'potencia' : pot.potencia
                    })
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['tensio'] = get_description(step.tensio_suministre, "TABLA_64")
        result['data_activacio'] = dateformat(step.data_activacio)
        return result
