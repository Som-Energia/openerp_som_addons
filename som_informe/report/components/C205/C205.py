from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC2 import ProcesC2

class C205(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C205'
        result['tipus_contracte'] =  get_description(step.tipus_contracte, "TABLA_9")
        result['tipus_autoconsum'] =  get_description(step.tipus_autoconsum, "TABLA_113")
        result['codi_contracte'] = step.contracte_atr
        result ['potencies'] = []
        for pot in step.pot_ids:
            result['potencies'].append({
                    'name' : pot.name,
                    'potencia' : pot.potencia
                })
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['tensio'] = get_description(step.tensio_suministre, "TABLA_64")
        result['data_activacio'] = step.data_activacio

        """
        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
            ('request_code','=',step.sw_id.codi_sollicitud),
            ('tipus','=','export'),
            ('proces','=','C2'),
            ('pas','=', '05'),
            ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)

        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)
        """

        return result