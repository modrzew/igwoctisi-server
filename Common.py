# -*- coding: utf-8 *-*
import Model
from datetime import datetime
import time
import json
import hashlib

h = hashlib.new('sha1')

def consoleMessage(msg):
	now = datetime.today()
	print('[' + now.strftime('%H:%M:%S') + '] ' + msg)

def jsonMessage(type, object, id):
	return json.dumps({'type': type, 'object': object, 'id': id})

def jsonError(code, id):
	return jsonMessage('error', code, id)

def jsonOk(id):
	return jsonMessage('ok', None, id)


def randomId():
	h.update(str(time.time()))
	return h.hexdigest()[0:12]
