from ..component_utils import get_description
from ..ProcesR1 import ProcesR1


class R105(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "R105"
        step02 = self.get_step_02(wiz, cursor, uid, step)
        result["codi_reclamacio_distri"] = (
            step02.codi_reclamacio_distri if step02 else "ERROR sense pas 02!!"
        )
        result["documents_adjunts"] = [
            (get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids
        ]
        result["comentaris_distri"] = step.comentaris
        result["resultat"] = get_description(step.resultat, "TABLA_80")
        detail_obj = wiz.pool.get("giscedata.switching.detalle.resultado")
        ids = detail_obj.search(cursor, uid, [("name", "=", step.detall_resultat)])
        if ids:
            detall = detail_obj.read(cursor, uid, ids[0], ["text"])["text"]
            result["detall_resultat"] = detall
        else:
            result["detall_resultat"] = step.detall_resultat
        return result
