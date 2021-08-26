from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesB1 import ProcesB1

class B107(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'B107'
        result['data_rebuig'] = dateformat(step.data_rebuig)
        result['rebutjos'] = [{'codi':rebuig.motiu_rebuig.name, 'descripcio' : rebuig.desc_rebuig} for rebuig in step.rebuig_ids]
        return result
