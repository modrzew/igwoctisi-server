# -*- coding: utf-8 *-*
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

engine = create_engine('mysql://%s:%s@%s/%s' % (CONFIG['username'], CONFIG['password'], CONFIG['host'], CONFIG['database']), pool_recycle=3600*24)
connection = engine.connect()
meta = MetaData()

class Schema:
	global engine
	users = Table('users', meta, autoload=True, autoload_with=engine)

def login(username, password):
	global connection
	s = select([func.count('*')]).where(and_(Schema.users.c.username == username, Schema.users.c.password == password)).select_from(Schema.users)
	rs = connection.execute(s)
	row = rs.fetchone()
	return row[0] == 1
