# -*- coding: utf-8 *-*
from datetime import datetime
import math
import random

LOG_FILE = None


def console_message(msg):
	now = datetime.today()
	output = '[' + now.strftime('%H:%M:%S') + '] ' + msg
	print(output)
	if LOG_FILE:
		LOG_FILE.write(output + '\n')

def json_message(type, object, id):
	return {'header': {'type': type, 'id': id}, 'object': object}

def json_error(code, id):
	return json_message('error', {'errorType': code}, id)

def json_ok(id):
	return json_message('ok', None, id)

def weighted_round(x):
	tmp = x - int(x)
	rnd = random.random()
	if rnd <= tmp:
		return int(math.ceil(x))
	else:
		return int(math.floor(x))
