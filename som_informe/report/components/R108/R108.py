from ..ProcesR1 import ProcesR1

class R108(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'R108'
        step02 = self.get_step_02(wiz, cursor, uid, step)
        result['codi_reclamacio_distri'] = step02.codi_reclamacio_distri
        return result