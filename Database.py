# -*- coding: utf-8 *-*
from django.contrib.auth import user_logged_in
from sqlalchemy import *
from sqlalchemy.sql import select
from sqlalchemy.pool import StaticPool

CONFIG = {
	'host': '127.0.0.1',
	'username': 'igwoctisi',
	'password': 'zpi',
	'database': 'igwoctisi'
#	'host': 'mysql.mydevil.net',
#	'username': 'm12056_igwoctisi',
#	'password': 'zpi',
#	'database': 'm12056_igwoctisi'
}

ENGINE = create_engine('mysql://%s:%s@%s/%s' % (CONFIG['username'], CONFIG['password'], CONFIG['host'], CONFIG['database']), pool_recycle=3600*24)
CONNECTION = None
USING_DATABASE = False
META = MetaData()

class Schema:
	global ENGINE
	users = Table('users', META, autoload=True, autoload_with=ENGINE)

def connect():
	global CONNECTION, USING_DATABASE
	CONNECTION = ENGINE.connect()
	USING_DATABASE = True

def login(username, password):
	global CONNECTION
	s = select([func.count('*')]).where(and_(Schema.users.c.username == username, Schema.users.c.password == password)).select_from(Schema.users)
	rs = CONNECTION.execute(s)
	row = rs.fetchone()
	return row[0] == 1
