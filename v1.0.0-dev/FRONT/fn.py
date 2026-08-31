import datetime
import os
import time
import traceback
import json
from PyQt6 import QtWidgets
"""
일반적으로 사용하는 공통함수 
"""
is_debug = True

# region 프로그램 관련 함수

#endregion

# region COMMON function
def fmti(value):
    return "{:,}".format(value)

def fmt(value, precision):
    return str(round(value, precision))

def filename_just(path):
    return os.path.basename(os.path.splitext(path)[0])

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def duration(start):
    return round(time.time() - start, 2)

def cut(value):
    return round(value, 3)

def error(ex):
    print(":: ERR :: " + str(ex))
    if is_debug : print(traceback.format_exc())
    #exit(1)

def warn(ex):
    print(":: WARNING :: " + str(ex))
    if is_debug : print(traceback.format_exc())

def debug(msg):
    if is_debug : print('DEBUG : ', msg)

def nullto(param, default=''):
    if param is None or param == '':
        return default
    else:
        return param

def unique_time():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')

def filename(path):
    return os.path.basename(path)

def filename_just(path):
    return os.path.basename(os.path.splitext(path)[0])

def intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False

def confirm(obj, msg):
    reply = QtWidgets.QMessageBox.question(obj, 'Confirm', msg,
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                           QtWidgets.QMessageBox.No)
    return reply == QtWidgets.QMessageBox.Yes
#endregion

