from gestionatr.utils import get_description
from ..ProcesE1 import ProcesE1

class E102(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'E102'
        result['rebuig'] = step.rebuig
        result['rebutjos'] = []
        for rebuig in step.rebuig_ids:
            result['rebutjos'].append({
                    'codi' : rebuig.motiu_rebuig.name,
                    'descripcio' : rebuig.desc_rebuig
                })
        result['data_rebuig'] = step.data_rebuig


        return result
