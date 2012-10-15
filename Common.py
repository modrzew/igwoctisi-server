# -*- coding: utf-8 *-*
from datetime import datetime
import time
import json
import hashlib

h = hashlib.new('sha1')

def console_message(msg):
	now = datetime.today()
	print('[' + now.strftime('%H:%M:%S') + '] ' + msg)

def json_message(type, object, id):
	return {'header': {'type': type, 'id': id}, 'object': object}

def json_error(code, id):
	return json_message('error', {'errorType': code}, id)

def json_ok(id):
	return json_message('ok', None, id)

def random_id():
	h.update(str(time.time()))
	return h.hexdigest()[0:12]
