# -*- coding: utf-8 *-*
from sqlalchemy import *
from sqlalchemy.sql import select
import hmac
import hashlib

ENGINE = None
CONNECTION = None
USING_DATABASE = False
META = None
CONFIG = None

class Schema:
	pass

def connect():
	try:
		import Config
	except ImportError:
		raise Exception('Config module not found')

	CONFIG = Config.DATABASE

	global CONFIG, ENGINE, CONNECTION, USING_DATABASE, META
	ENGINE = create_engine('mysql://%s:%s@%s/%s' % (CONFIG['username'], CONFIG['password'], CONFIG['host'], CONFIG['database']), pool_recycle=3600*24)
	CONNECTION = ENGINE.connect()
	META = MetaData()
	USING_DATABASE = True

	Schema.users = Table('users', META, autoload=True, autoload_with=ENGINE)

def login(username, password):
	global CONNECTION
	s = select([func.count('*')]).where(and_(Schema.users.c.username == username, Schema.users.c.password == password)).select_from(Schema.users)
	rs = CONNECTION.execute(s)
	row = rs.fetchone()
	return row[0] == 1
