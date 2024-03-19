from ..component_utils import dateformat, get_description
from ..ProcesM1 import ProcesM1


class M105(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "M105"
        result["tipus_autoconsum"] = get_description(step.tipus_autoconsum, "TABLA_113")
        result["control_potencia"] = get_description(step.control_potencia, "TABLA_51", True)
        result["potencies"] = [
            {"name": pot.name, "potencia": pot.potencia}
            for pot in step.pot_ids
            if pot.potencia != 0
        ]
        result["tarifa"] = get_description(step.tarifaATR, "TABLA_17")
        result["data_activacio"] = dateformat(step.data_activacio)

        step01 = self.get_step_01(wiz, cursor, uid, step)
        result["tipus_sol"] = step01.sollicitudadm if step01 else "ERROR sense pas 01!!"
        result["tensio_sol"] = step01.tensio_solicitada if step01 else "ERROR sense pas 01!!"
        return result
