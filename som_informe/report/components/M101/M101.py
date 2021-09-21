from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesM1 import ProcesM1

class M101(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'M101'
        result['sol_tensio'] = step.solicitud_tensio
        result['tensio_sol'] = step.tensio_solicitada
        result['tipus_sol'] = step.sollicitudadm
        result['potencies'] = [{'name':pot.name, 'potencia':pot.potencia} for pot in step.pot_ids if pot.potencia != 0]
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['telefons'] = [{'numero':telefon.numero} for telefon in step.telefons]
        result['canvi_titular'] = step.canvi_titular
        result['nom'] = step.nom
        result['cognom1'] = step.cognom_1
        result['cognom2'] = step.cognom_2
        result['document_identificatiu'] = get_description(step.tipus_document, "TABLA_6")
        if step.codi_document[:1] == 'ES':
            result['codi_document'] = step.codi_document[2:]
        else:
            result['codi_document'] = step.codi_document
        result['tipus_autoconsum'] =  get_description(step.tipus_autoconsum, "TABLA_113")
        if step.control_potencia:
            result['control_potencia'] =  get_description(step.control_potencia, "TABLA_51")
        result['comentaris'] = step.comentaris
        if len(step.document_ids) == 0:
            result['adjunts'] = False

        try:
            swl_obj = step.pool.get('giscedata.switching.log')

            search_params = [
                ('request_code','=',step.sw_id.codi_sollicitud),
                ('tipus','=','export'),
                ('proces','=','M1'),
                ('pas','=', '01'),
                ('status', '=', 'correcte')
            ]
            swl_ids = swl_obj.search(cursor, uid, search_params)

            if len(swl_ids) > 0:
                swl = swl_obj.browse(cursor, uid, swl_ids[0])
                result['day'] = dateformat(swl.case_date)
            else:
                result['day'] = u"Not Found"
        except Exception as e:
            result['day'] = u"Access Error"
        return result