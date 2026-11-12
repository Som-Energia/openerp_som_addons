# -*- coding: utf-8 -*-
from ..component_utils import get_description
from ..ProcesR1 import ProcesR1


class R101(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "R101"
        result["tipus_reclamacio"] = (
            step.subtipus_id.name + " - " + step.subtipus_id.desc if step.subtipus_id else ""
        )
        result["text"] = step.comentaris
        result["documents_adjunts"] = [
            (get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids
        ]
        result["variables_aportacio"] = []
        for var_apo in step.vars_aportacio_info_ids:
            result["variables_aportacio"].append(
                {
                    "valor": var_apo.valor,
                    "variable": get_description(var_apo.variable, "TABLA_76"),
                    "descripcio": var_apo.desc_peticio_info,
                    "tipus": get_description(var_apo.tipus_info, "TABLA_85"),
                }
            )

        result["reclamacions"] = []

        for reclama in step.reclamacio_ids:
            lectures = []
            for lect in reclama.lect_ids:
                lectures.append(
                    {
                        "lectura": lect.lectura,
                        "magnitud": lect.magnitud,
                        "nom": lect.name,
                    }
                )
            aten_incorr = False
            concept_facturat = False
            par_contr = False
            if reclama.tipus_atencio_incorrecte:
                aten_incorr = get_description(reclama.tipus_atencio_incorrecte, "TABLA_87_simple")
            if reclama.tipus_concepte_facturat:
                concept_facturat = get_description(reclama.tipus_concepte_facturat, "TABLA_77")
            if reclama.parametre_contractacio:
                par_contr = get_description(reclama.parametre_contractacio, "TABLA_79")
            result["reclamacions"].append(
                {
                    "codi_dh": reclama.codi_dh,
                    "codi_incidencia": reclama.codi_incidencia,
                    "codi_postal": reclama.codi_postal,
                    "codi_solicitud": reclama.codi_sollicitud,
                    "codi_solicitud_reclamacio": reclama.codi_sollicitud_reclamacio,
                    "concepte_disconformitat": reclama.concepte_disconformitat,
                    "cont_email": reclama.cont_email,
                    "cont_nom": reclama.cont_nom,
                    "cont_prefix": reclama.cont_prefix,
                    "cont_telefon": reclama.cont_telefon,
                    "data_fins": reclama.data_fins,
                    "data_incident": reclama.data_incident,
                    "data_inici": reclama.data_inici,
                    "data_lectura": reclama.data_lectura,
                    "descripcio_ubicacio": reclama.desc_ubicacio,
                    "IBAN": reclama.iban,
                    "import_reclamat": reclama.import_reclamat,
                    "municipi": reclama.municipi.name if reclama.municipi else False,
                    "numero_expedient_escomesa": reclama.num_expedient_escomesa,
                    "numero_expedient_frau": reclama.num_expedient_frau,
                    "numero_factura": reclama.num_factura,
                    "parametre_contractacio": par_contr,
                    "poblacio": reclama.poblacio.name if reclama.poblacio else False,
                    "provincia": reclama.provincia.name if reclama.provincia else False,
                    "tipus_atencio_incorrecte": aten_incorr,
                    "tipus_concepte_facturat": concept_facturat,
                    "lectures": lectures,
                }
            )
        return result
