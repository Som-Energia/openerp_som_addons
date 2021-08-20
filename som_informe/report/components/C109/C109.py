from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC1 import ProcesC1

class C109(ProcesC1.ProcesC1):
    def __init__(self):
        ProcesC1.ProcesC1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC1.ProcesC1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C109'
        result['data_creacio'] = dateformat(step.date_created)
        result['rebuig'] = step.rebuig
        result['rebutjos'] = []
        for rebuig in step.rebuig_ids:
            result['rebutjos'].append({
                    'descripcio' : rebuig.desc_rebuig
                })

        return result