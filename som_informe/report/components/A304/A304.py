from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3

class A304(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A304'
        result['data_rebuig'] = dateformat(step.data_rebuig)
        result['rebuigs'] = []
        for rebuig in step.rebuig_ids:
            result['rebuigs'].append({
                    'codi_rebuig' : rebuig.id,
                    'comentari' : rebuig.desc_rebuig
            })
        return result
