# -*- coding: utf-8 -*-
from datetime import datetime,timedelta

def val(object):
    return getattr(object, 'val', object)

def dateformat(date):
    return datetime.strptime(val(date), '%Y-%m-%d').strftime('%d/%m/%Y')

def getYMDdate(date):
    return datetime.strptime(date, '%Y-%m-%d')