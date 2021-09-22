from gestionatr.utils import get_description
from ..ProcesD1 import ProcesD1
from ..component_utils import dateformat

class D102(ProcesD1.ProcesD1):
    def __init__(self):
        ProcesD1.ProcesD1.__init__(self)

    def step_name(self):
        return '02'

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesD1.ProcesD1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'D102'
        result['rebuig'] = step.rebuig
        result['rebutjos'] = [{'codi':rebuig.motiu_rebuig.name, 'descripcio' : rebuig.desc_rebuig} for rebuig in step.rebuig_ids]
        result['day'] = self.get_log_date(wiz, cursor, uid, step)
        return result
