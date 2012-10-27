# -*- coding: utf-8 *-*
from sqlalchemy import *
from sqlalchemy.sql import select
from sqlalchemy.pool import StaticPool

engine = create_engine('sqlite:///IGWOCTISI.db', connect_args={'check_same_thread':False}, poolclass=StaticPool, echo=True)
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
