from ..component_utils import get_description
from ..ProcesR1 import ProcesR1


class R103(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "R103"
        result["codi_reclamacio_distri"] = step.codi_reclamacio_distri
        result["hi_ha_info_intermitja"] = step.hi_ha_info_intermitja
        result["hi_ha_retipificacio"] = step.hi_ha_retipificacio
        result["tipologia_retifica"] = (
            step.retip_tipus + " - " + step.retip_subtipus_id.desc if step.retip_subtipus_id else ""
        )
        result["hi_ha_sol_info_retip"] = step.hi_ha_sol_info_retip
        result["tipologia_sol_retip"] = (
            step.sol_retip_tipus + " - " + step.sol_retip_subtipus_id.desc
            if step.sol_retip_subtipus_id
            else ""
        )
        result["hi_ha_solicitud"] = step.hi_ha_sollicitud
        result["documents_adjunts"] = [
            (get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids
        ]
        result["comentaris_distri"] = step.comentaris
        result["tipus_comunicacio"] = get_description(step.tipus_comunicacio, "TABLA_84")
        return result
