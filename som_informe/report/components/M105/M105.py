from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesM1 import ProcesM1

class M105(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'M105'
        result['tipus_autoconsum'] =  get_description(step.tipus_autoconsum, "TABLA_113")
        if step.control_potencia and step.control_potencia != '':
            result['control_potencia'] =  get_description(step.control_potencia, "TABLA_51")
        result['potencies'] = [{'name':pot.name, 'potencia':pot.potencia} for pot in step.pot_ids if pot.potencia != 0]
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['data_activacio'] = dateformat(step.data_activacio)

        swl_obj = step.pool.get('giscedata.switching')

        swl_ids = swl_obj.browse(cursor, uid, step.sw_id.id)
        model_obj = step.pool.get(swl_ids.step_ids[0].pas_id.split(',')[0])

        result['tipus_sol'] =  model_obj.read(cursor, uid, (swl_ids.step_ids[0].pas_id).split(',')[1])[0]['sollicitudadm']
        if model_obj.read(cursor, uid, (swl_ids.step_ids[0].pas_id).split(',')[1])[0]['tensio_solicitada']:
            result['tensio_sol'] = get_description(model_obj.read(cursor, uid, (swl_ids.step_ids[0].pas_id).split(',')[1])[0]['tensio_solicitada'], "TABLA_64")
        return result