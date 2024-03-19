from ..component_utils import dateformat, get_description
from ..ProcesC2 import ProcesC2


class C201(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def step_name(self):
        return "01"

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result["type"] = "C201"
        result["tipologia_solicitud"] = step.sollicitudadm
        result["canvi_titular"] = step.canvi_titular
        result["nom"] = step.nom
        result["primer_cognom"] = step.cognom_1
        result["segon_cognom"] = step.cognom_2
        result["document_acreditatiu"] = get_description(step.tipus_document, "TABLA_6")
        if step.codi_document[:1] == "ES":
            result["codi_document"] = step.codi_document[2:]
        else:
            result["codi_document"] = step.codi_document
        result["tipus_contracte"] = get_description(step.tipus_contracte, "TABLA_9")
        result["tipus_autoconsum"] = get_description(step.tipus_autoconsum, "TABLA_113")
        result["control_potencia"] = get_description(step.control_potencia, "TABLA_51", True)
        result["potencies"] = [
            {"name": pot.name, "potencia": pot.potencia}
            for pot in step.pot_ids
            if pot.potencia != 0
        ]
        result["tarifa"] = get_description(step.tarifaATR, "TABLA_17")
        if step.tensio_solicitada:
            result["tensio"] = get_description(step.tensio_solicitada, "TABLA_64")
        result["comentaris"] = step.comentaris
        if len(step.document_ids) == 0:
            result["adjunts"] = False
        start_date = self.get_log_date(wiz, cursor, uid, step)
        if start_date:
            result["day"] = dateformat(start_date)
            result["date"] = start_date

        return result
