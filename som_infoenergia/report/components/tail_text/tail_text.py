from datetime import datetime, timedelta

class tail_text():

    def get_data(self, cursor, uid, object, extra_text, context):
        if object.polissa_id:
            if object.polissa_id.modcontractual_activa:
                data_limit_ingres = datetime.strptime(object.polissa_id.modcontractual_activa.data_final,"%Y-%m-%d") - timedelta(days=7)
                data_limit_ingres = data_limit_ingres.strftime("%d-%m-%Y")
            else:
                data_limit_ingres = "ERROR no mod con activa"
        else:
            data_limit_ingres = "ERROR no polissa"
        return {
            'data_limit_ingres': data_limit_ingres,
            'import_garantia': extra_text.get("import_garantia", "ERROR EXTRA TEXT: sense import garantia"),
        }
