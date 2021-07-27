from ..component_utils import dateformat
from ..ProcesR1 import ProcesR1

class R101(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, cursor, uid, step)
        result['type'] = 'R101'
        result['tipus_reclamacio'] = step.subtipus_id.name + " - " + step.subtipus_id.desc if step.subtipus_id else ''
        result['text'] = step.comentaris
        return result