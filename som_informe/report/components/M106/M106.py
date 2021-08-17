from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesM1 import ProcesM1

class M106(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'M106'
        result['data_creacio'] = step.date_created
        return result