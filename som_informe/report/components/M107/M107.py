from ..component_utils import dateformat
from ..ProcesM1 import ProcesM1

class M107(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'M107'
        result['rebuig'] = step.rebuig
        result['data_creacio'] = dateformat(step.date_created)
        result['rebutjos'] = []
        for rebuig in step.rebuig_ids:
            result['rebutjos'].append({
                    'descripcio' : rebuig.desc_rebuig
                })

        return result