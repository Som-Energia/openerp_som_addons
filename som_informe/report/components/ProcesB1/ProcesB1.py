from ..ProcesATR import ProcesATR


class ProcesB1(ProcesATR.ProcesATR):
    def __init__(self):
        ProcesATR.ProcesATR.__init__(self)

    def proces_name(self):
        return "B1"

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesATR.ProcesATR.get_data(self, wiz, cursor, uid, step)
        return result
