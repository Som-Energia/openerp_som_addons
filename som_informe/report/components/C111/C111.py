from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC1 import ProcesC1

class C111(ProcesC1.ProcesC1):
    def __init__(self):
        ProcesC1.ProcesC1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC1.ProcesC1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C111'
        result['data_activacio'] = dateformat(step.data_activacio)


        return result