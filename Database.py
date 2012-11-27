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
	global CONFIG, ENGINE, CONNECTION, USING_DATABASE, META

	try:
		import Config
	except ImportError:
		raise Exception('Config module not found')

	CONFIG = Config.DATABASE
	ENGINE = create_engine('mysql://%s:%s@%s/%s' % (CONFIG['username'], CONFIG['password'], CONFIG['host'], CONFIG['database']), pool_recycle=3600*24)
	CONNECTION = ENGINE.connect()
	META = MetaData()
	USING_DATABASE = True

	Schema.users = Table('users', META, autoload=True, autoload_with=ENGINE)
	Schema.games = Table('games', META, autoload=True, autoload_with=ENGINE)
	Schema.places = Table('places', META, autoload=True, autoload_with=ENGINE)

def login(username, password):
	global CONNECTION
	s = select(['id']).where(and_(Schema.users.c.username == username, Schema.users.c.password == password)).select_from(Schema.users)
	rs = CONNECTION.execute(s)
	row = rs.fetchone()
	if row is None:
		return -1
	else:
		return row['id']

def create_game(game):
	global CONNECTION
	values = {
		'name': game.name,
	}
	ins = insert(Schema.games, values=values)
	result = CONNECTION.execute(ins)
	game.id = result.inserted_primary_key[0]


def save_game(game):
	global CONNECTION
	values = {
		'time': game.time
	}
	where = {
		'id': game.id
	}
	CONNECTION.execute(update(Schema.games).where(Schema.games.c.id==game.id).values(values))
	places = game.players_lost + game.players
	places.reverse()
	for p in places:
		values = {
			'game_id': game.id,
			'user_id': p.id,
			'place': places.index(p) + 1,
			'points': 0
		}
		ins = insert(Schema.places, values)
		CONNECTION.execute(ins)
		# TODO jak zrobic update users set points=points+x
		#CONNECTION.execute(update(Schema.users).where(Schema.user.c.id==p.id).values(values))
