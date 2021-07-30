from datetime import datetime

def dateformat(str_date, hours = False):
    if not str_date:
        return ""
    if not hours:
        return datetime.strptime(str_date[0:10],'%Y-%m-%d').strftime('%d-%m-%Y')
    return datetime.strptime(str_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
