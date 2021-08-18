from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesB1 import ProcesB1

class B107(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'B107'
        result['data_rebuig'] = step.data_rebuig
        result['rebuigs'] = []
        for rebuig in step.rebuig_ids:
            result['rebuigs'].append({
                    'codi_rebuig' : rebuig.id,
                    'comentari' : rebuig.desc_rebuig
            })
        return result
