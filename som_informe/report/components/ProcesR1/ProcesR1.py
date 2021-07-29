from ..component_utils import dateformat

class ProcesR1():
    def __init__(self):
        pass

    def get_step_02(self, wiz, cursor, uid, step):
        return self.get_step(wiz, cursor, uid, step, '02')

    def get_step(self, wiz, cursor, uid, step, step_name):
        for sub_step in step.sw_id.step_ids:
            if sub_step.step_id.name == step_name:
                r_model,r_id = sub_step.pas_id.split(',')
                model_obj = wiz.pool.get(r_model)
                return model_obj.browse(cursor, uid, int(r_id))
        return None

    def get_data(self, wiz, cursor, uid, step):
        result = {}
        result['date'] = step.date_created
        result['day'] = dateformat(step.date_created)
        result['create'] = dateformat(step.date_created, True)
        result['pas'] = step.sw_id.step_id.name
        result['codi_solicitud'] = step.sw_id.codi_sollicitud
        result['titol'] = step.sw_id.proces_id.name + " - " + step.sw_id.step_id.name
        result['distribuidora'] = step.sw_id.partner_id.name
        return result
