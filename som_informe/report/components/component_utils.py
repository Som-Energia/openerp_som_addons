from gestionatr.utils import get_description as gestion_atr_get_description
from datetime import datetime

def dateformat(str_date, hours = False):
    if not str_date:
        return ""
    if not hours:
        return datetime.strptime(str_date[0:10],'%Y-%m-%d').strftime('%d-%m-%Y')
    return datetime.strptime(str_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')

def get_description(key, table_name, on_error_return_false = False):
    try:
        return gestion_atr_get_description(key, table_name)
    except (ValueError, KeyError):
        if on_error_return_false:
            return False
        return "ERROR {} no trobat a {}.".format(key, table_name)

def is_domestic(pol):
    for cat in pol.category_id:
        if cat.code == 'DOM':
            return True
    return False

def is_enterprise(pol):
    return not is_domestic(pol)