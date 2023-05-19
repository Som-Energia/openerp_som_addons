from ..ProcesA3 import ProcesA3


class A307(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result["type"] = "A307"
        result["rebuig"] = step.rebuig
        result["rebutjos"] = [
            {"codi": rebuig.motiu_rebuig.name, "descripcio": rebuig.desc_rebuig}
            for rebuig in step.rebuig_ids
        ]
        return result
