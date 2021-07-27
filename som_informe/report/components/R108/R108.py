from ..ProcesR1 import ProcesR1

class R108(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, cursor, uid, step)
        result['type'] = 'R101'
        return result