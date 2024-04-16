from ..component_utils import dateformat, get_description
from ..ProcesM1 import ProcesM1


class M101(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def step_name(self):
        return "01"

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "M101"
        result["sol_tensio"] = step.solicitud_tensio
        result["tensio_sol"] = step.tensio_solicitada
        result["tipus_sol"] = step.sollicitudadm
        result["potencies"] = [
            {"name": pot.name, "potencia": pot.potencia}
            for pot in step.pot_ids
            if pot.potencia != 0
        ]
        result["tarifa"] = get_description(step.tarifaATR, "TABLA_17")
        result["telefons"] = [{"numero": telefon.numero} for telefon in step.telefons]
        result["canvi_titular"] = step.canvi_titular
        result["nom"] = step.nom
        result["cognom1"] = step.cognom_1
        result["cognom2"] = step.cognom_2
        result["document_identificatiu"] = get_description(step.tipus_document, "TABLA_6")
        if step.codi_document[:1] == "ES":
            result["codi_document"] = step.codi_document[2:]
        else:
            result["codi_document"] = step.codi_document
        result["tipus_autoconsum"] = get_description(step.tipus_autoconsum, "TABLA_113")
        result["control_potencia"] = get_description(step.control_potencia, "TABLA_51", True)
        result["comentaris"] = step.comentaris
        if len(step.document_ids) == 0:
            result["adjunts"] = False
        start_date = self.get_log_date(wiz, cursor, uid, step)
        if start_date:
            result["day"] = dateformat(start_date)
            result["date"] = start_date
        return result
