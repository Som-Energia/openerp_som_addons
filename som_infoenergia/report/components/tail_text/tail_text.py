from datetime import datetime, timedelta
import calendar

class tail_text():

    def get_data(self, cursor, uid, object, extra_text, context):
        def leap_replace(data,year):
            if data.month == 2 and data.day == 29 and not calendar.isleap(year):
                return datetime(year,2,28)
            return datetime(year,data.month,data.day)

        def get_renovation_date_dt(data_alta):
            today = datetime.now()
            alta = datetime.strptime(data_alta, '%Y-%m-%d')
            reno = leap_replace(alta, today.year)
            if reno < today:
                reno = leap_replace(alta, today.year +1)
            return reno

        if object.polissa_id:
            if object.polissa_id.data_alta:
                data_limit_ingres = get_renovation_date_dt(object.polissa_id.data_alta) - timedelta(days=7)
                data_limit_ingres = data_limit_ingres.strftime("%d-%m-%Y")
            else:
                data_limit_ingres = "ERROR no data alta"

        else:
            data_limit_ingres = "ERROR no polissa"
        return {
            'data_limit_ingres': data_limit_ingres,
            'import_garantia': extra_text.get("import_garantia", "ERROR EXTRA TEXT: sense import garantia"),
        }
