from ..component_utils import get_description
from ..ProcesD1 import ProcesD1


class D101(ProcesD1.ProcesD1):
    def __init__(self):
        ProcesD1.ProcesD1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesD1.ProcesD1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "D101"
        result["motiu_canvi"] = (get_description(step.motiu_canvi, "TABLA_109"),)
        result["CAU"] = step.cau
        if step.seccio_registre:
            result["seccio_registre"] = get_description(step.seccio_registre, "TABLA_127")
        else:
            result["seccio_registre"] = False
        result["subseccio"] = step.subseccio
        result["CUPS"] = step.cups
        result["generadors"] = []
        for gen in step.generadors:
            if gen.identificador[:1] == "ES":
                aux = gen.identificador[2:]
            else:
                aux = gen.identificador
            result["generadors"].append(
                {
                    "potencia_instalada": gen.pot_installada_gen,
                    "tec_generador": gen.tec_generador,
                    "tipus_instalacio": get_description(gen.tipus_installacio, "TABLA_129"),
                    "SSAA": gen.ssaa,
                    "ref_cadastre": gen.ref_cadastre_inst_gen,
                    "nom": gen.nom,
                    "cognom1": gen.cognom_1,
                    "cognom2": gen.cognom_2,
                    "email_contacte": gen.email,
                    "tipus_document": get_description(gen.tipus_identificador, "TABLA_6"),
                    "document": aux,
                }
            )
        result["comentaris"] = step.comentaris
        return result
